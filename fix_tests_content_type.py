import glob
import re

for path in glob.glob("tests/*.py"):
    with open(path, "r") as f:
        content = f.read()
    
    # Replace content_type="application/json" and json parameter
    content = re.sub(r'data=_json\.dumps\((.*?)\),\s*content_type="application/json"', r'json=\1', content)
    content = re.sub(r'data=json\.dumps\((.*?)\),\s*content_type="application/json"', r'json=\1', content)
    
    # Also handle some tests that do content_type='application/json'
    content = re.sub(r"data=_json\.dumps\((.*?)\),\s*content_type='application/json'", r'json=\1', content)
    content = re.sub(r"data=json\.dumps\((.*?)\),\s*content_type='application/json'", r'json=\1', content)
    
    # In test_webhook.py, the body is encoded to bytes: body = json.dumps(payload).encode()
    # client.post(..., data=body, content_type="application/json") -> client.post(..., content=body, headers={"Content-Type": "application/json"})
    content = content.replace('content_type="application/json"', 'headers={"Content-Type": "application/json"}')

    # Wait, Starlette TestClient takes `content=body` for bytes, not `data=body` (data is for form data). 
    # Actually `content` is correct for httpx/Starlette.
    content = content.replace('data=body,', 'content=body,')

    with open(path, "w") as f:
        f.write(content)

