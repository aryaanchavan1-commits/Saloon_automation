import os
import json
import streamlit as st
from openai import OpenAI
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

SYSTEM_PROMPT = """You are SaloonAI, an expert business analytics AI for a premium salon management system.
Analyze the salon data provided and give:

1. **Monthly Performance Summary** - revenue trends, customer growth, peak days
2. **Revenue Analysis** - profit margins after expenses & salaries, average transaction value
3. **Customer Insights** - repeat customer ratio, top spenders, churn risk
4. **Staff Analysis** - cost vs revenue contribution, efficiency
5. **Expense Optimization** - where to cut costs, recurring expense impact
6. **Actionable Recommendations** - specific steps to increase revenue & retention
7. **Predictive Insights** - forecast next month trends

Format with clear sections, emojis, and bullet points. Be specific with numbers.
Keep responses concise but data-rich. Always highlight the most critical insight first."""

def get_api_key():
    try:
        return st.secrets["opencode"]["api_key"]
    except (KeyError, AttributeError):
        pass
    try:
        from database import SessionLocal, SaloonSetting
        db = SessionLocal()
        setting = db.query(SaloonSetting).filter(SaloonSetting.key == "opencode_api_key").first()
        db.close()
        if setting and setting.value:
            return setting.value
    except:
        pass
    return ""

def set_api_key_in_db(key):
    from database import SessionLocal, SaloonSetting
    from datetime import datetime
    db = SessionLocal()
    try:
        setting = db.query(SaloonSetting).filter(SaloonSetting.key == "opencode_api_key").first()
        if setting:
            setting.value = key
            setting.updated_at = datetime.now()
        else:
            db.add(SaloonSetting(key="opencode_api_key", value=key))
        db.commit()
    except:
        db.rollback()
    finally:
        db.close()

def get_ai_client():
    api_key = get_api_key()
    if not api_key:
        st.error("OpenCode Zen API key not configured. Set it in Saloon Settings.")
        return None
    return OpenAI(
        api_key=api_key,
        base_url="https://api.opencode.ai/v1"
    )

def analyze_dashboard_data(data_summary):
    content, error = _call_ai_api([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyze this salon data and provide insights:\n\n{json.dumps(data_summary, indent=2)}"}
    ])
    if content:
        return content
    return f"⚠️ AI analysis error: {error}"

def get_revenue_prediction(monthly_data):
    content, error = _call_ai_api([
        {"role": "system", "content": "You are a revenue forecasting AI. Based on monthly revenue data, predict next month revenue. Return ONLY a JSON: {\"prediction\": number, \"confidence\": \"high/medium/low\", \"trend\": \"up/down/stable\", \"reason\": \"short reason\"}"},
        {"role": "user", "content": f"Monthly revenue data (last 12 months): {json.dumps(monthly_data)}"}
    ])
    if not content:
        return None
    try:
        text = content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("\n", 1)[0]
            if text.endswith("```"):
                text = text[:-3]
        return json.loads(text)
    except:
        return None

def get_customer_suggestion(customer_data):
    content, error = _call_ai_api([
        {"role": "system", "content": "You are a salon CRM AI. Suggest personalized offers & retention strategies for customers. Be concise."},
        {"role": "user", "content": f"Customer data: {json.dumps(customer_data)}"}
    ])
    return content

CHAT_SYSTEM_PROMPT = """You are SaloonAI, an expert business assistant for a premium salon management system.
You have access to the salon's complete business data including revenue, customers, transactions, expenses, staff, inventory, and appointments.

Rules:
1. Answer questions based ONLY on the data provided in the context below.
2. If the data doesn't contain the answer, say "I don't have that information in your salon data."
3. Be concise and specific with numbers and figures.
4. Use natural, conversational language.
5. You can analyze trends, suggest improvements, and generate reports from the data.
6. Format responses with bullet points and sections for readability.
7. Always mention specific amounts in ₹ when discussing financial data.
8. Never make up data — only use what's in the context."""

def _call_ai_api(messages):
    """Try OpenAI client, fall back to direct HTTP request."""
    api_key = get_api_key()
    if not api_key:
        return None, "API key not configured"

    # Try OpenAI client first
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.opencode.ai/v1")
        response = client.chat.completions.create(
            model="DeepSeek V4 Flash Free",
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )
        if response and hasattr(response, "choices") and response.choices:
            content = response.choices[0].message.content
            if content:
                return content, None
        return None, f"Unexpected response format: {type(response).__name__}"
    except Exception as e:
        err_msg = str(e)

    # Fallback: direct HTTP request
    if HAS_REQUESTS:
        try:
            resp = requests.post(
                "https://api.opencode.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={"model": "DeepSeek V4 Flash Free", "messages": messages, "temperature": 0.7, "max_tokens": 1500},
                timeout=60
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    return content, None
                return None, "API returned empty content"
            else:
                return None, f"API HTTP {resp.status_code}: {resp.text[:300]}"
        except Exception as e2:
            return None, f"Direct call also failed: {err_msg} / {str(e2)}"
    else:
        return None, err_msg

def chat_with_saloon_data(user_message, data_context):
    """Send a chat message with salon data context and get AI response."""
    content, error = _call_ai_api([
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "user", "content": f"""Here is the current salon business data context:

{json.dumps(data_context, indent=2)}

User question: {user_message}"""}
    ])
    if content:
        return content
    return f"⚠️ AI response error: {error}"
