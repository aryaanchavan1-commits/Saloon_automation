import os
import json
import streamlit as st
from openai import OpenAI

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
    client = get_ai_client()
    if not client:
        return "⚠️ AI agent not configured. Set your OpenCode Zen API key in Settings."

    try:
        response = client.chat.completions.create(
            model="DeepSeek V4 Flash Free",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this salon data and provide insights:\n\n{json.dumps(data_summary, indent=2)}"}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI analysis error: {str(e)}"

def get_revenue_prediction(monthly_data):
    client = get_ai_client()
    if not client:
        return None
    try:
        response = client.chat.completions.create(
            model="DeepSeek V4 Flash Free",
            messages=[
                {"role": "system", "content": "You are a revenue forecasting AI. Based on monthly revenue data, predict next month revenue. Return ONLY a JSON: {\"prediction\": number, \"confidence\": \"high/medium/low\", \"trend\": \"up/down/stable\", \"reason\": \"short reason\"}"},
                {"role": "user", "content": f"Monthly revenue data (last 12 months): {json.dumps(monthly_data)}"}
            ],
            temperature=0.3,
            max_tokens=300
        )
        text = response.choices[0].message.content
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("\n", 1)[0]
            if text.endswith("```"):
                text = text[:-3]
        return json.loads(text)
    except:
        return None

def get_customer_suggestion(customer_data):
    client = get_ai_client()
    if not client:
        return None
    try:
        response = client.chat.completions.create(
            model="DeepSeek V4 Flash Free",
            messages=[
                {"role": "system", "content": "You are a salon CRM AI. Suggest personalized offers & retention strategies for customers. Be concise."},
                {"role": "user", "content": f"Customer data: {json.dumps(customer_data)}"}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except:
        return None
