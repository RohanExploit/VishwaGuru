import os
from google import genai
from typing import Optional
import json

# Configure Gemini
# Use provided key as fallback if env var is missing
api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyB8_i3tbDE3GmX4CsQ8G3mD3pB2WrHi5C8")
client = None
if api_key:
    client = genai.Client(api_key=api_key)

async def generate_action_plan(issue_description: str, category: str, image_path: Optional[str] = None) -> dict:
    """
    Generates an action plan (WhatsApp message, Email draft) using Gemini.
    """
    if not client:
        return {
            "whatsapp": f"Hello, I would like to report a {category} issue: {issue_description}",
            "email_subject": f"Complaint regarding {category}",
            "email_body": f"Respected Authority,\n\nI am writing to bring to your attention a {category} issue: {issue_description}.\n\nPlease take necessary action.\n\nSincerely,\nCitizen"
        }

    try:
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

        response = await client.aio.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        text_response = response.text.strip()

        # Cleanup if markdown code blocks are returned
        if text_response.startswith("```json"):
            text_response = text_response[7:-3]
        elif text_response.startswith("```"):
            text_response = text_response[3:-3]

        return json.loads(text_response)

    except Exception as e:
        print(f"Gemini Error: {e}")
        # Fallback
        return {
            "whatsapp": f"Hello, I would like to report a {category} issue: {issue_description}",
            "email_subject": f"Complaint regarding {category}",
            "email_body": f"Respected Authority,\n\nI am writing to bring to your attention a {category} issue: {issue_description}.\n\nPlease take necessary action.\n\nSincerely,\nCitizen"
        }

async def chat_with_civic_assistant(query: str, history: Optional[list] = None) -> str:
    """
    Chat with the civic assistant.
    """
    if not client:
        return "I am currently offline. Please try again later."

    try:
        prompt = f"""
        You are VishwaGuru, a helpful civic assistant for Indian citizens.
        User Query: {query}

        Answer the user's question about civic issues, government services, or local administration.
        If they ask about specific MLAs, tell them to use the "Find My MLA" feature.
        Keep answers concise and helpful.
        """

        response = await client.aio.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini Chat Error: {e}")
        return "I encountered an error processing your request."
