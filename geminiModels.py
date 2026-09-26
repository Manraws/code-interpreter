# check_models.py
import os
import requests

API_KEY = os.environ["GEMINI_API_KEY"]  # or however you load it (.env, etc.)

response = requests.get(
    "https://generativelanguage.googleapis.com/v1beta/models",
    params={"key": API_KEY}
)
response.raise_for_status()

for model in response.json()["models"]:
    # only show models that support generateContent (the method you're calling)
    if "generateContent" in model.get("supportedGenerationMethods", []):
        print(model["name"], "-", model.get("displayName"))