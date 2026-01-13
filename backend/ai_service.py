import json
import os
import warnings
from functools import lru_cache
from typing import Optional

import google.generativeai as genai
from async_lru import alru_cache

# Suppress deprecation warnings from google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

RESPONSIBILITY_MAP_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "responsibility_map.json",
)

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

@lru_cache(maxsize=1)
def _load_responsibility_map() -> dict:
    """Load responsibility map for authority tagging."""
    try:
        with open(RESPONSIBILITY_MAP_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def build_x_post(issue_description: str, category: str) -> str:
    """
    Build an X.com (Twitter) post tagging the relevant authority when available.
    """
    responsibility_map = _load_responsibility_map()
    category_key = str(category).lower().replace(" ", "_")
    authority_info = responsibility_map.get(category_key, {})
    handle = authority_info.get("twitter")

    base_message = f"Reporting a {category} issue: {issue_description[:200]}"
    if handle:
        return f"{base_message} Tagging {handle} for prompt action. #CivicIssue #VishwaGuru"
    return f"{base_message} #CivicIssue #VishwaGuru"


async def generate_action_plan(issue_description: str, category: str, image_path: Optional[str] = None) -> dict:
    """
    Generates an action plan (WhatsApp message, Email draft, X.com post) using Gemini.
    """
    x_post = build_x_post(issue_description, category)

    if not api_key:
        return {
            "whatsapp": f"Hello, I would like to report a {category} issue: {issue_description}",
            "email_subject": f"Complaint regarding {category}",
            "email_body": f"Respected Authority,\n\nI am writing to bring to your attention a {category} issue: {issue_description}.\n\nPlease take necessary action.\n\nSincerely,\nCitizen",
            "x_post": x_post,
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
        4. A concise X.com post text (max 240 chars). If provided, prefer this authority handle for tagging: {x_post}

        Return the response in strictly valid JSON format with keys: "whatsapp", "email_subject", "email_body", "x_post".
        Do not use markdown code blocks. Just the raw JSON string.
        """

        response = await model.generate_content_async(prompt)
        text_response = response.text.strip()

        # Cleanup if markdown code blocks are returned
        if "```json" in text_response:
             text_response = text_response.split("```json")[1].split("```")[0]
        elif "```" in text_response:
             text_response = text_response.split("```")[1].split("```")[0]

        text_response = text_response.strip()

        try:
            plan = json.loads(text_response)
        except json.JSONDecodeError:
            # Try to fix common JSON errors if possible, or fallback
            print(f"Gemini returned invalid JSON: {text_response}")
            raise Exception("Invalid JSON from AI")

        if "x_post" not in plan or not plan.get("x_post"):
            plan["x_post"] = x_post
        return plan

    except Exception as e:
        print(f"Gemini Error: {e}")
        # Fallback
        return {
            "whatsapp": f"Hello, I would like to report a {category} issue: {issue_description}",
            "email_subject": f"Complaint regarding {category}",
            "email_body": f"Respected Authority,\n\nI am writing to bring to your attention a {category} issue: {issue_description}.\n\nPlease take necessary action.\n\nSincerely,\nCitizen",
            "x_post": x_post,
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
