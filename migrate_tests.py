import os
import glob
import re

test_files = glob.glob("tests/*.py")

for file_path in test_files:
    with open(file_path, "r") as f:
        content = f.read()

    # Imports
    content = content.replace("from flask import", "# from flask import")
    if "from fastapi.testclient import TestClient" not in content:
        content = content.replace("from src.main import app", "from src.main import app\nfrom fastapi.testclient import TestClient")

    # Client instantiation
    content = content.replace("app.test_client()", "TestClient(app)")

    # JSON extraction
    content = content.replace(".get_json()", ".json()")

    with open(file_path, "w") as f:
        f.write(content)

print(f"Migrated {len(test_files)} test files.")
