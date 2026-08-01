import re

with open("src/api/routes.py", "r") as f:
    content = f.read()

# 1. Remove the jsonify_wrapper definition if it's there
content = re.sub(r'def jsonify\(.*?\):\n.*?return kwargs\n', '', content, flags=re.DOTALL)

# 2. Replace JSONResponse(content=jsonify( ... )) with JSONResponse(content= ... )
# Easiest way is to remove `content=jsonify(` -> `content=`
content = content.replace("content=jsonify(", "content=")

# Now we have an extra `)` where `jsonify` used to close.
# Case 1: `}), status_code=400)` -> `}, status_code=400)`
content = content.replace("}), status_code=", "}, status_code=")

# Case 2: `})` at the end of a multi-line JSONResponse which had no status code.
# `    })` -> `    })` wait! If it was `return JSONResponse(content=jsonify({\n...\n})`, 
# we changed it to `return JSONResponse(content={\n...\n})` so `})` is actually correct! 
# Wait, if it was `jsonify({...})`, removing `jsonify(` leaves `content={...})`.
# So `})` is exactly `} ` + `)` (the closing paren for JSONResponse).
# Let's check:
# original: return JSONResponse(content=jsonify({\n"a": 1\n}))
# after removing jsonify(: return JSONResponse(content={\n"a": 1\n}))
# So we need to replace `}))` with `})`?
# Wait, earlier I noticed line 626 to 630 was:
# return JSONResponse(content=jsonify({
#   "imported": len(ok), ...
# })
# It was ALREADY missing the closing `)` for jsonify!
# So replacing `content=jsonify(` with `content=` actually fixes it and leaves `})` which perfectly closes `JSONResponse`!
# What about single line calls?
# `return JSONResponse(content=jsonify({"error": "..."}), status_code=400)`
# After removing `jsonify(`, it becomes `return JSONResponse(content={"error": "..."}, status_code=400)` 
# Wait, earlier I did `content = content.replace("}), status_code=", "}, status_code=")`
# which turns it into `return JSONResponse(content={"error": "..."}, status_code=400)` which is perfect!

# What about single line without status code?
# `return JSONResponse(content=jsonify({"error": "..."}))`
# After removing `jsonify(`, it becomes `return JSONResponse(content={"error": "..."}))`
# So we need to replace `}))\n` with `})\n`
content = content.replace("}))\n", "})\n")

with open("src/api/routes.py", "w") as f:
    f.write(content)
