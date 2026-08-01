import glob

for path in glob.glob("tests/*.py"):
    with open(path, "r") as f:
        content = f.read()
    
    content = content.replace('app.config["TESTING"] = True', '# app.config["TESTING"] = True')
    
    # We also need to fix test_webhook.py if it accesses request headers using Werkzeug EnvironHeaders
    # or anything else specific. Let's just fix the config first.
    with open(path, "w") as f:
        f.write(content)

