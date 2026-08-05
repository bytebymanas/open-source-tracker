"""
Authentication routes using GitHub OAuth and JWT.
"""

import os
import httpx
import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from src.models.database import Database
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
db = Database()

JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_development_key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
# Comma-separated list of github usernames to automatically make admins
ADMIN_GITHUB_USERNAMES = [u.strip() for u in os.getenv("ADMIN_GITHUB_USERNAMES", "").split(",") if u.strip()]

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return {"username": username, "role": role}
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user

def require_mentor_or_admin(user: dict = Depends(get_current_user)):
    role = user.get("role")
    if role not in ["mentor", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Mentor or Admin privileges required")
    return user

@router.get("/github/login")
def github_login():
    if not GITHUB_CLIENT_ID:
        return JSONResponse(status_code=500, content={"error": "oauth_not_configured", "message": "GITHUB_CLIENT_ID not set"})
    
    redirect_uri = "http://127.0.0.1:5000/api/auth/github/callback"
    url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri={redirect_uri}&scope=read:user"
    return RedirectResponse(url)

@router.get("/github/callback")
async def github_callback(code: str, response: Response):
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        return JSONResponse(status_code=500, content={"error": "oauth_not_configured", "message": "OAuth secrets not set"})
    
    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code
            }
        )
        token_data = token_res.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            return JSONResponse(status_code=400, content={"error": "oauth_error", "message": "Failed to retrieve access token"})
        
        # Fetch user profile
        user_res = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_data = user_res.json()
        
    username = user_data.get("login")
    if not username:
        return JSONResponse(status_code=400, content={"error": "oauth_error", "message": "Could not get GitHub username"})
        
    # Check if user should be an admin
    role = "admin" if username in ADMIN_GITHUB_USERNAMES else "student"
    
    # Upsert user into database
    db.upsert_user(
        github_username=username,
        github_id=user_data.get("id"),
        name=user_data.get("name") or username,
        avatar_url=user_data.get("avatar_url"),
        role=role
    )
    
    # We must ensure the role matches what is actually in the DB (in case they were already a mentor)
    # The upsert_user doesn't downgrade roles due to our COALESCE logic, so let's fetch the real role
    db_user = db.get_user(username)
    real_role = db_user.get("role", "student")
    
    jwt_token = create_access_token(data={"sub": username, "role": real_role})
    
    redirect_res = RedirectResponse(url="/")
    redirect_res.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        max_age=JWT_EXPIRATION_HOURS * 3600,
        samesite="lax"
    )
    return redirect_res

@router.get("/me")
def get_me(user: dict = Depends(get_current_user)):
    db_user = db.get_user(user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return limited info to frontend
    return {
        "username": db_user["github_username"],
        "name": db_user["name"],
        "avatar_url": db_user["avatar_url"],
        "role": db_user["role"],
        "department": db_user["department"],
        "university": db_user["university"]
    }

@router.post("/logout")
def logout():
    response = JSONResponse(content={"status": "ok", "message": "Logged out"})
    response.delete_cookie(key="access_token")
    return response
