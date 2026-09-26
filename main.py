

# in bash export AIPIPE_TOKEN="someKey"
# or in powershell $env:AIPIPE_TOKEN="YOUR_TOKEN_HERE" 



from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

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

# AI Error Analysis

import os
from pydantic import BaseModel
from google import genai
from google.genai import types
from typing import List



client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))  # uses GEMINI_API_KEY or GOOGLE_API_KEY env var
possibleGenModelList = []

for model in client.models.list():
    if "generateContent" in model.supported_actions:
        print(model.name)
        possibleGenModelList.append(model.name)

class ErrorAnalysis(BaseModel):
    error_lines: List[int]  # Line numbers with errors

def analyze_error_with_ai(code: str, traceback: str) -> List[int]:
    """
    Use LLM with structured output to identify error line numbers.
    """
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    prompt = f"""
Analyze this Python code and its error traceback.
Identify the line number(s) where the error occurred.

CODE:
{code}

TRACEBACK:
{traceback}

Return the line number(s) where the error is located.
"""

    response = client.models.generate_content(
        # model=possibleGenModelList[0], # take the first model , generating error 
        model="gemini-3.8-flash",
        # model='gemini-2.0-flash-exp',
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
