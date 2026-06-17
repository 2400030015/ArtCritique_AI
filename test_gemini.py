from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-2.5-pro")

response = model.generate_content(
    "Say hello to my AI Art Critic project."
)

print(response.text)