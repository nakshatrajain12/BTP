import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# We expect GEMINI_API_KEY in the environment
client = genai.Client()

import time

def summarize_scheme(scheme_data: dict) -> str:
    prompt = f"Summarise this government startup scheme in 3 sentences in plain English. Focus on: who can apply, how much they can get, and what the main benefit is.\n\nScheme Data: {scheme_data}"
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt,
            )
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))
            else:
                print(f"Failed summarize_scheme: {e}")
                return "Pending summary due to high AI load."

def recommend_schemes(user_sector: str, user_stage: str, user_location: str, schemes_list: list) -> str:
    prompt = f"Given these schemes:\n{schemes_list}\n\nRecommend the top 3 for a {user_stage} startup in {user_sector} based in {user_location}. Explain the specific reason each scheme fits. Return JSON: [{{name, reason, application_url}}]"
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt,
            )
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))
            else:
                raise e

def chat_with_agent(message: str, history: list, context_data: str) -> str:
    messages_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
    prompt = f"You are GOV-BOT, an AI expert on Indian government startup schemes and policies.\nYou have been loaded with knowledge about these schemes.\nHelp the user understand eligibility, application process, required documents, funding amounts, deadlines, and any other details.\nBe specific, accurate, and helpful. If you don't know something, say so.\nContext Data:\n{context_data}\n\nChat History:\n{messages_str}\n\nUser: {message}\nAI:"
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return "Sorry, I am facing some issues connecting to my brain right now."
