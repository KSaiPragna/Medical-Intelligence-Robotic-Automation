# MIRA – Health Prediction AI

A professional healthcare dashboard built with Streamlit, SQLite, and AI-assisted medical remark generation.

## Project Overview
MIRA is a polished junior AI/ML developer technical assessment application that:
- Manages patient blood test data with full CRUD operations
- Stores patient records in SQLite
- Generates intelligent health remarks using GROQ with graceful fallback
- Provides a modern hospital-grade dashboard and analytics pages
- Includes strong validation and production-ready architecture

## Features
- Dashboard with key health metrics
- Add, view, update, and delete patient records
- AI-powered health prediction remarks
- Analytics visualization using Plotly
- Responsive medical UI with sidebar navigation

## Tech Stack
- Python
- Streamlit
- SQLite
- Pandas
- Plotly
- GROQ API (optional)
- Python Dotenv

## Installation
1. Clone the repository.
2. Create a Python virtual environment.
3. Install dependencies:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:

```env
GROQ_API_KEY=
GROQ_MODEL=gpt-3.5-turbo
GROQ_ENDPOINT=https://api.groq.com/v1
```

5. Run the app:

```bash
streamlit run app.py
```

## Deployment
This application is Streamlit-ready and can be deployed on:
- Streamlit Cloud
- Render
- Hugging Face Spaces

## Notes
- The `.env` file should never expose your API key publicly.
- The application initializes sample patient data on first launch.
- AI generation falls back to local rule-based remarks if the external API is unavailable.
- The optional Kaggle lab dataset is available in `assets/laboratory__data.csv` for expanded analytics.
- This lab dataset is useful for disease and lab-value analysis, while the patient CRUD workflow still uses name/DOB/email-backed records.

## Folder Structure
```
MIRA NEW/
│── app.py
│── database.py
│── ai_prediction.py
│── requirements.txt
│── README.md
│── .env
│── patients.db
│── assets/
│── style.css
```