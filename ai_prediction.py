import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "gpt-3.5-turbo")
GROQ_ENDPOINT = os.getenv("GROQ_ENDPOINT", "https://api.groq.com/v1")


def _construct_health_context(glucose, haemoglobin, cholesterol):
    conditions = []
    if glucose >= 126:
        conditions.append("elevated glucose consistent with diabetes risk")
    elif glucose >= 100:
        conditions.append("borderline elevated glucose")

    if cholesterol >= 240:
        conditions.append("high cholesterol with cardiovascular risk")
    elif cholesterol >= 200:
        conditions.append("borderline high cholesterol")

    if haemoglobin < 12.5:
        conditions.append("low haemoglobin suggestive of anemia")
    elif haemoglobin <= 13.5:
        conditions.append("haemoglobin in the lower normal range")

    if not conditions:
        conditions.append("blood profile within expected healthy ranges")

    return conditions


def _build_prompt(glucose, haemoglobin, cholesterol):
    prompt = (
        "You are a professional medical AI assistant. "
        "Build one concise but clinical comment based on the following blood test values. "
        "Do not use overly technical jargon. "
        f"Glucose: {glucose} mg/dL, Haemoglobin: {haemoglobin} g/dL, Cholesterol: {cholesterol} mg/dL. "
        "Include a clinical recommendation and risk area if relevant. "
        "Example output: Patient blood profile indicates elevated glucose and cholesterol levels. "
        "There may be an increased risk of diabetes and cardiovascular complications. "
        "Recommend clinical consultation and lifestyle monitoring."
    )
    return prompt


def _local_remark(glucose, haemoglobin, cholesterol):
    conditions = _construct_health_context(glucose, haemoglobin, cholesterol)
    summary = ", ".join(conditions)
    risk_phrases = []

    if glucose >= 126:
        risk_phrases.append("diabetes")
    elif glucose >= 100:
        risk_phrases.append("glucose intolerance")

    if cholesterol >= 240:
        risk_phrases.append("cardiovascular complications")
    elif cholesterol >= 200:
        risk_phrases.append("cardiovascular risk")

    if haemoglobin < 12.5:
        risk_phrases.append("anemia")

    if risk_phrases:
        risk_clause = " and ".join(risk_phrases)
        recommendation = (
            f"Patient blood profile indicates {summary}. "
            f"There may be an increased risk of {risk_clause}. "
            "Recommend clinical consultation, dietary review, and lifestyle monitoring."
        )
    else:
        recommendation = (
            f"Patient blood profile indicates {summary}. "
            "Continue preventive health maintenance with regular screening and balanced nutrition."
        )
    return recommendation


def _call_groq(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a professional medical assistant specializing in patient blood test interpretation."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 180,
    }
    response = requests.post(GROQ_ENDPOINT, headers=headers, json=payload, timeout=12)
    response.raise_for_status()
    data = response.json()
    if "choices" in data and data["choices"]:
        choice = data["choices"][0]
        if "message" in choice and "content" in choice["message"]:
            return choice["message"]["content"].strip()
        if "text" in choice:
            return choice["text"].strip()
    return ""


def generate_health_remark(glucose, haemoglobin, cholesterol):
    """Generate a professional medical remark using GROQ when available."""
    try:
        glucose = float(glucose)
        haemoglobin = float(haemoglobin)
        cholesterol = float(cholesterol)
    except (TypeError, ValueError):
        return _local_remark(glucose, haemoglobin, cholesterol)

    if GROQ_API_KEY:
        try:
            prompt = _build_prompt(glucose, haemoglobin, cholesterol)
            text = _call_groq(prompt)
            if text:
                return re.sub(r"\s+", " ", text)
        except Exception:
            return _local_remark(glucose, haemoglobin, cholesterol)

    return _local_remark(glucose, haemoglobin, cholesterol)
