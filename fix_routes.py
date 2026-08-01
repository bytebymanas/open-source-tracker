import re

with open("src/api/routes.py", "r") as f:
    content = f.read()

# 1. Add Body import
if "from fastapi import" in content and "Body" not in content:
    content = content.replace("from fastapi import APIRouter", "from fastapi import APIRouter, Body")

# 2. Add Request to GET signatures where request is used.
content = content.replace("def export_leaderboard():", "def export_leaderboard(request: Request):")
content = content.replace("def list_annotations():", "def list_annotations(request: Request):")
content = content.replace("def get_leaderboard():", "def get_leaderboard(request: Request):") # Wait, is it get_leaderboard or something else? Let's check my grep output:
# Line 181: period = request.query_params.get("period", "all_time") -> This is get_leaderboard. Let's do it safely:
content = re.sub(r'def get_leaderboard\((.*?)\):', r'def get_leaderboard(request: Request):', content)
# wait, it might have been get_leaderboard() with no args.
content = content.replace("def get_leaderboard():", "def get_leaderboard(request: Request):")

# 3. Replace POST/PATCH body injection
content = content.replace("def import_students():", "def import_students(body: dict = Body(default={})):")
content = content.replace("def update_student(username):", "def update_student(username: str, body: dict = Body(default={})):")
content = content.replace("def update_annotation(annotation_id):", "def update_annotation(annotation_id: int, body: dict = Body(default={})):")
content = content.replace("def update_weights():", "def update_weights(body: dict = Body(default={})):")
content = content.replace("def add_annotation(contribution_id):", "def add_annotation(contribution_id: int, body: dict = Body(default={})):")
# Now remove request.get_json() logic since we already have body
content = re.sub(r'body = request\.get_json\(.*?\) or \{\}', '', content)
content = re.sub(r'data = request\.get_json\(.*?\)', 'data = body', content)

# 4. Fix jsonify
content = re.sub(r'return jsonify\((.*?)\), (\d+)', r'return JSONResponse(status_code=\2, content=\1)', content)
content = re.sub(r'return jsonify\((.*?)\)', r'return JSONResponse(content=\1)', content)
# There are some multi-line jsonify calls
# we can just import jsonify and define it as a wrapper in routes.py!
jsonify_wrapper = """
def jsonify(*args, **kwargs):
    if args and isinstance(args[0], dict):
        return args[0]
    return kwargs
"""
if "def jsonify" not in content:
    content = content.replace("from fastapi.responses import JSONResponse", "from fastapi.responses import JSONResponse\n" + jsonify_wrapper)
    content = content.replace("return jsonify", "return JSONResponse(content=jsonify")
    # Actually that might break if we already replaced it in part 1. Let's just fix the specific multi-line jsonify we saw.
    
    # "return jsonify({"
    # "    "error": "invalid_payload","
    # ...
    content = content.replace("return jsonify({", "return JSONResponse(content={")
    content = re.sub(r'\}\), (\d+)', r'}, status_code=\1)', content)

with open("src/api/routes.py", "w") as f:
    f.write(content)
