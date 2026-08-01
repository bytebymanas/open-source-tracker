import re
import os

filepath = "src/api/routes.py"
with open(filepath, "r") as f:
    content = f.read()

# 1. Imports
content = content.replace(
    "from flask import Blueprint, jsonify, request, Response",
    "from fastapi import APIRouter, Request, Response\nfrom fastapi.responses import JSONResponse\nfrom pydantic import BaseModel\nfrom typing import List, Optional, Dict, Any\nimport json as _json"
)

# 2. Router initialization
content = content.replace(
    'api = Blueprint("api", __name__, url_prefix="/api")',
    'router = APIRouter()'
)

# 3. Decorators
content = re.sub(r'@api\.route\("(.*?)", methods=\["GET"\]\)', r'@router.get("\1")', content)
content = re.sub(r'@api\.route\("(.*?)", methods=\["POST"\]\)', r'@router.post("\1")', content)
content = re.sub(r'@api\.route\("(.*?)", methods=\["PATCH"\]\)', r'@router.patch("\1")', content)
content = re.sub(r'@api\.route\("(.*?)", methods=\["DELETE"\]\)', r'@router.delete("\1")', content)

# Flask route params like <username> to FastAPI {username}
content = re.sub(r'<int:(.*?)>', r'{\1}', content)
content = re.sub(r'<(.*?)>', r'{\1}', content)

# 4. Request args -> query_params
content = content.replace("request.args.get", "request.query_params.get")

# 5. Return JSONResponse
# jsonify(X), 200 -> JSONResponse(content=X)
content = re.sub(r'return jsonify\((.*?)\), (\d+)', r'return JSONResponse(status_code=\2, content=\1)', content)
# jsonify(X) without status code -> JSONResponse(content=X)
content = re.sub(r'return jsonify\((.*?)\)(?!\s*,)', r'return JSONResponse(content=\1)', content)

# 6. For endpoints with JSON bodies, we have to change the function signature to accept request: Request, and make it async.
# Wait, if we make it async, SQLite fails with "ProgrammingError: SQLite objects created in a thread can only be used in that same thread" 
# because FastAPI will run it on the main thread (event loop), but Database() creates a connection.
# Actually, if we use standard `def`, FastAPI runs it in a separate thread.
# If we change it to `async def`, it runs in the main thread.
# BUT, `request.json()` in FastAPI is async! So we MUST make it async if we use `Request`.
# A better way is to use Pydantic models and keep `def`.
pass

with open("src/api/routes_migrated.py", "w") as f:
    f.write(content)
