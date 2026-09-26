

# in bash export AIPIPE_TOKEN="someKey"
# or in powershell $env:AIPIPE_TOKEN="YOUR_TOKEN_HERE" 



from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()



#enable cors
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or your specific frontend origin
    allow_methods=["*"],
    allow_headers=["*"],
)

# to exec the code from request

# Tool Function (execute_python_code)

def execute_python_code(code: str) -> dict:
    """
    Execute Python code and return exact output.

    Returns:
        {
            "success": bool,
            "output": str  # Exact stdout or traceback
        }
    """
    import sys
    from io import StringIO
    import traceback

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        # Execute code
        exec(code)
        output = sys.stdout.getvalue()
        return {"success": True, "output": output}

    except Exception as e:
        # Get full traceback
        output = traceback.format_exc()
        return {"success": False, "output": output}

    finally:
        sys.stdout = old_stdout




# in bash export GEMINI_API_KEY="someKey"
# or in powershell $env:GEMINI_API_KEY="YOUR_TOKEN_HERE"
# in bash export GEMINI_API_KEY="someKey"
# or in powershell $env:GEMINI_API_KEY="YOUR_TOKEN_HERE"

# AI Error Analysis

import os
import time
from pydantic import BaseModel
from google import genai
from google.genai import types, errors
from typing import List


client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
possibleGenModelList = []

for model in client.models.list():
    if "generateContent" in model.supported_actions:
        print(model.name)
        possibleGenModelList.append(model.name)

PREFERRED_MODELS = ["models/gemini-2.5-flash", "models/gemini-2.5-flash-lite", "models/gemini-2.0-flash"]
ACTIVE_MODEL = next((m for m in PREFERRED_MODELS if m in possibleGenModelList),
                     possibleGenModelList[0] if possibleGenModelList else None)
print(f"Using model: {ACTIVE_MODEL}")


class ErrorAnalysis(BaseModel):
    error_lines: List[int]  # Line numbers with errors


def analyze_error_with_ai(code: str, traceback: str) -> List[int]:
    """
    Use LLM with structured output to identify error line numbers.
    Falls back to [] if Gemini is unavailable or fails.
    """
    if ACTIVE_MODEL is None:
        return []

    prompt = f"""
Analyze this Python code and its error traceback.
Identify the line number(s) where the error occurred.

CODE:
{code}

TRACEBACK:
{traceback}

Return the line number(s) where the error is located.
"""

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=ACTIVE_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "error_lines": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(type=types.Type.INTEGER)
                            )
                        },
                        required=["error_lines"]
                    )
                )
            )
            result = ErrorAnalysis.model_validate_json(response.text)
            return result.error_lines
        except errors.ServerError as e:
            print(f"Gemini server error (attempt {attempt + 1}/{max_retries + 1}): {e}")
            if attempt < max_retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            return []
        except Exception as e:
            print(f"analyze_error_with_ai failed: {e}")
            return []



# basic app to capture request

@app.get("/")
def home():
    return {"message": "Code Interpreter API is running"}

class CodeRequest(BaseModel):
    code: str


# @app.post("/code-interpreter")
# def code_interpreter(request: CodeRequest):
#     return {
#         "received_code": request.code
#     }

# @app.post("/code-interpreter")
# def code_interpreter(request: CodeRequest):
#     execution = execute_python_code(request.code)

#     return execution

@app.post("/code-interpreter")
def code_interpreter(request: CodeRequest):

    execution = execute_python_code(request.code)

    if execution["success"]:
        return {
            "error": [],
            "result": execution["output"]
        }

    error_lines = analyze_error_with_ai(
        request.code,
        execution["output"]
    )

    return {
        "error": error_lines,
        "result": execution["output"]
    }
# test the function
# print(execute_python_code("x = 5\ny = 10\nprint(x + y)"))
