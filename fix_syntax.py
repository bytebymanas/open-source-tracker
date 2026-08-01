import re

with open("src/api/routes.py", "r") as f:
    content = f.read()

# The incorrect replacement was:
# return JSONResponse(content=jsonify({
#   "error": "..."
# }, status_code=400)
#
# We need to change `}, status_code=XXX)` to `}), status_code=XXX)`

content = re.sub(r'\}, status_code=(\d+)\)', r'}), status_code=\1)', content)

# But wait, did I miss the parenthesis for the JSONResponse call?
# original: return jsonify({...}), 400
# what I have now: return JSONResponse(content=jsonify({...}), status_code=400)
# Wait! Let's trace it.
# `return jsonify({` -> `return JSONResponse(content=jsonify({`
# `}), 400` -> `}, status_code=400)`
# Resulting line:
# return JSONResponse(content=jsonify({ ... }, status_code=400) -> Wait, there is no closing paren for JSONResponse!
# It should be `}), status_code=400)` (for jsonify) and then `)` for JSONResponse.
# So `return JSONResponse(content=jsonify({...}), status_code=400)`
# This means `}, status_code=400)` should be `}), status_code=400)`

# Wait! Does jsonify wrapper accept status_code? No, jsonify_wrapper was just `def jsonify(*args, **kwargs): return args[0]`
# The JSONResponse takes `status_code`.
# `JSONResponse(content=jsonify({...}), status_code=400)`
# So I should replace `\}, status_code=(\d+)\)` with `}), status_code=\1)`
content = re.sub(r'\}, status_code=(\d+)\)', r'}), status_code=\1)', content)

with open("src/api/routes.py", "w") as f:
    f.write(content)
