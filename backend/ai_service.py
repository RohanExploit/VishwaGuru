"""
AI Service Module - Gemini Integration

Provides AI-powered services for VishwaGuru using Google's Generative AI (Gemini).
Includes action plan generation for civic issues and an interactive civic assistant chatbot.
"""
import os
import google.generativeai as genai
from typing import Optional
import warnings
from async_lru import alru_cache

# Suppress deprecation warnings from google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

# Configure Gemini
# Use provided key as fallback if env var is missing
api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyB8_i3tbDE3GmX4CsQ8G3mD3pB2WrHi5C8")
if api_key:
    genai.configure(api_key=api_key)

async def generate_action_plan(
    issue_description: str, 
    category: str, 
    image_path: Optional[str] = None
) -> dict:
    """Generate WhatsApp message and email draft for reporting issue to authorities."""
    if not api_key:
        return {
            "whatsapp": f"Hello, I would like to report a {category} issue: {issue_description}",
            "email_subject": f"Complaint regarding {category}",
            "email_body": f"Respected Authority,\n\nI am writing to bring to your attention a {category} issue: {issue_description}.\n\nPlease take necessary action.\n\nSincerely,\nCitizen"
        }

    try:
        # Use Gemini 1.5 Flash for faster response times
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""
        You are a civic action assistant. A user has reported a civic issue.
        Category: {category}
        Description: {issue_description}

        Please generate:
        1. A concise WhatsApp message (max 200 chars) that can be sent to authorities.
        2. A formal but firm email subject.
        3. A formal email body (max 150 words) addressed to the relevant authority (e.g., Municipal Commissioner, Police, etc. based on category).

        Return the response in strictly valid JSON format with keys: "whatsapp", "email_subject", "email_body".
        Do not use markdown code blocks. Just the raw JSON string.
        """

        response = await model.generate_content_async(prompt)
        text_response = response.text.strip()

        # Cleanup if markdown code blocks are returned
        if text_response.startswith("```json"):
            text_response = text_response[7:-3]
        elif text_response.startswith("```"):
            text_response = text_response[3:-3]

        import json
        return json.loads(text_response)

    except Exception as e:
        print(f"Gemini Error: {e}")
        # Fallback
        return {
            "whatsapp": f"Hello, I would like to report a {category} issue: {issue_description}",
            "email_subject": f"Complaint regarding {category}",
            "email_body": f"Respected Authority,\n\nI am writing to bring to your attention a {category} issue: {issue_description}.\n\nPlease take necessary action.\n\nSincerely,\nCitizen"
        }

@alru_cache(maxsize=100)
async def chat_with_civic_assistant(query: str) -> str:
    """Answer questions on civic issues using Gemini. Results cached (100 entries)."""
    if not api_key:
        return "I am currently offline. Please try again later."

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""
        You are VishwaGuru, a helpful civic assistant for Indian citizens.
        User Query: {query}

        Answer the user's question about civic issues, government services, or local administration.
        If they ask about specific MLAs, tell them to use the "Find My MLA" feature.
        Keep answers concise and helpful.
        """

        response = await model.generate_content_async(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini Chat Error: {e}")
        return "I encountered an error processing your request."
