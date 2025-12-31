import os
import google.generativeai as genai
from typing import Optional, List, Dict, Any
import warnings
from async_lru import alru_cache
import json
import PIL.Image

# Suppress deprecation warnings from google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

# Configure Gemini
# Use provided key as fallback if env var is missing
api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyB8_i3tbDE3GmX4CsQ8G3mD3pB2WrHi5C8")
if api_key:
    genai.configure(api_key=api_key)

async def generate_action_plan(issue_description: str, category: str, image_path: Optional[str] = None) -> dict:
    """
    Generates an action plan (WhatsApp message, Email draft) using Gemini.
    """
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
async def chat_with_civic_assistant(query: str, history: List[dict] = []) -> str:
    """
    Chat with the civic assistant.
    """
    if not api_key:
        return "I am currently offline. Please try again later."

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Construct context from history
        history_context = ""
        if history:
            history_context = "Previous conversation:\n"
            for msg in history[-5:]: # Keep last 5 messages for context
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_context += f"{role}: {content}\n"

        prompt = f"""
        You are VishwaGuru, a helpful civic assistant for Indian citizens.
        {history_context}
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

async def analyze_issue_image(image_path: str) -> Dict[str, Any]:
    """
    Analyzes an image to detect the civic issue, category, and severity.
    """
    if not api_key:
        return {
            "description": "AI analysis unavailable",
            "category": "Uncategorized",
            "severity": "Unknown"
        }

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        if not os.path.exists(image_path):
             return {"error": "Image file not found"}

        img = PIL.Image.open(image_path)

        prompt = """
        Analyze this image of a civic issue.
        Identify:
        1. A short description of the issue.
        2. The category (e.g., Pothole, Garbage, Flooding, Vandalism, Street Light, etc.).
        3. The severity (Low, Medium, High).

        Return valid JSON with keys: "description", "category", "severity".
        """

        response = await model.generate_content_async([prompt, img])
        text_response = response.text.strip()

        if text_response.startswith("```json"):
            text_response = text_response[7:-3]
        elif text_response.startswith("```"):
            text_response = text_response[3:-3]

        return json.loads(text_response)

    except Exception as e:
        print(f"Gemini Image Analysis Error: {e}")
        return {
            "description": "Could not analyze image",
            "category": "Unknown",
            "severity": "Unknown"
        }

async def analyze_issue_with_ai(description: str, image_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyzes an issue description and optional image.
    """
    if not api_key:
        return {
             "category": "General",
             "severity": "Medium",
             "authority": "Local Municipal Corporation",
             "action_plan": "Report to local ward office."
        }

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        content = []
        prompt_text = f"""
        Analyze this civic issue report.
        Description: {description}

        Determine:
        1. The most appropriate Category.
        2. Severity Level (Low, Medium, High).
        3. Responsible Authority in India (e.g., BMC, Police, MSEB, etc.).
        4. A recommended Action Plan (short sentence).

        Return valid JSON with keys: "category", "severity", "authority", "action_plan".
        """
        content.append(prompt_text)

        if image_path and os.path.exists(image_path):
            img = PIL.Image.open(image_path)
            content.append(img)

        response = await model.generate_content_async(content)
        text_response = response.text.strip()

        if text_response.startswith("```json"):
            text_response = text_response[7:-3]
        elif text_response.startswith("```"):
            text_response = text_response[3:-3]

        return json.loads(text_response)

    except Exception as e:
        print(f"Gemini Analysis Error: {e}")
        return {
             "category": "General",
             "severity": "Medium",
             "authority": "Local Authority",
             "action_plan": "Please visit the nearest municipal office."
        }
