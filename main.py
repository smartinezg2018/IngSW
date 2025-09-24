import requests

# Replace with your actual API key
api_key = "AIzaSyDbFru5Yrx8RFGBQ3fOvOPsK4EDYXms1GI"
api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"

prompt = "What is the capital of France?"

payload = {
    "contents": [{"parts": [{"text": prompt}]}]
}

try:
    response = requests.post(api_url, json=payload)
    response.raise_for_status()
    result = response.json()
    text = result["candidates"][0]["content"]["parts"][0]["text"]
    print(f"Prompt: {prompt}\n")
    print(f"Response: {text}")
except Exception as e:
    print(f"An error occurred: {e}")