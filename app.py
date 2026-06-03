import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

import ai_prediction
import database


def load_css():
    try:
        with open("style.css", "r", encoding="utf-8") as style_file:
            st.markdown(f"<style>{style_file.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Style file not found. Using default layout.")


def calculate_age(dob_value):
    today = date.today()
    if isinstance(dob_value, str):
        dob_value = datetime.strptime(dob_value, "%Y-%m-%d").date()
    age = today.year - dob_value.year - ((today.month, today.day) < (dob_value.month, dob_value.day))
    return age


def is_valid_email(email_value):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
    return bool(re.match(pattern, email_value))


def validate_form(full_name, email, dob, glucose, haemoglobin, cholesterol):
    errors = []
    if not full_name.strip():
        errors.append("Full Name is required.")
    if not re.match(r"^[A-Za-z ]+$", full_name.strip()):
        errors.append("Full Name can only include alphabetic characters and spaces.")
    if not is_valid_email(email.strip()):
        errors.append("Please enter a valid email address.")
    if isinstance(dob, date) and dob > date.today():
        errors.append("Date of Birth cannot be in the future.")
    for label, value in [("Glucose", glucose), ("Haemoglobin", haemoglobin), ("Cholesterol", cholesterol)]:
        if value is None:
            errors.append(f"{label} is required.")
        elif value < 0:
            errors.append(f"{label} cannot be negative.")
    return errors


def format_patient_table(df: pd.DataFrame):
    if df.empty:
        return df
    df = df.copy()
    if "dob" in df.columns:
        df["age"] = df["dob"].apply(calculate_age)
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
    ordered_columns = [
        c for c in ["id", "full_name", "age", "dob", "email", "glucose", "haemoglobin", "cholesterol", "remarks", "created_at"] if c in df.columns
    ]
    if ordered_columns:
        return df[ordered_columns]
    return df


def load_lab_dataset():
    lab_path = Path("assets/laboratory__data.csv")
    if not lab_path.exists():
        return None
    df = pd.read_csv(lab_path)
    df = df.rename(columns={"Cholestrol": "Cholesterol"})
    if "Disease " in df.columns:
        df = df.rename(columns={"Disease ": "Disease"})
    return df


def render_dashboard(patients):
    st.markdown("## Dashboard Overview")
    if patients.empty:
        st.info("No patient records found. Add a new patient to get started.")
        return

    total_patients = len(patients)
    avg_glucose = patients["glucose"].mean()
    avg_haemoglobin = patients["haemoglobin"].mean()
    avg_cholesterol = patients["cholesterol"].mean()

    risk_counts = {
        "Diabetes Risk": int((patients["glucose"] >= 126).sum()),
        "Cholesterol Risk": int((patients["cholesterol"] >= 200).sum()),
        "Anemia Risk": int((patients["haemoglobin"] < 12.5).sum()),
    }

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Patients", total_patients)
    col2.metric("Avg. Glucose", f"{avg_glucose:.1f} mg/dL")
    col3.metric("Avg. Haemoglobin", f"{avg_haemoglobin:.1f} g/dL")
    col4.metric("Avg. Cholesterol", f"{avg_cholesterol:.1f} mg/dL")

    with st.container():
        chart1, chart2 = st.columns((2, 1))
        with chart1:
            fig = px.histogram(
                patients,
                x="glucose",
                nbins=12,
                labels={"glucose": "Glucose (mg/dL)"},
                title="Glucose Distribution",
                template="plotly_white",
            )
            fig.update_layout(margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
        with chart2:
            risk_df = pd.DataFrame(
                {"Risk Category": list(risk_counts.keys()), "Count": list(risk_counts.values())}
            )
            fig = px.pie(
                risk_df,
                names="Risk Category",
                values="Count",
                title="Risk Breakdown",
                color_discrete_sequence=px.colors.sequential.Blues,
            )
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("Recent Patient Records", expanded=True):
        st.dataframe(format_patient_table(patients), use_container_width=True)


def render_add_patient():
    st.markdown("## Add New Patient Record")
    with st.form("patient_form"):
        full_name = st.text_input("Full Name")
        dob = st.date_input("Date of Birth",
                value=date(2000, 1, 1),   # default DOB
                min_value=date(1900, 1, 1),  # allow old years
                max_value=date.today())
        email = st.text_input("Email Address")
        glucose = st.number_input("Glucose (mg/dL)", min_value=0.0, step=0.1, format="%.1f")
        haemoglobin = st.number_input("Haemoglobin (g/dL)", min_value=0.0, step=0.1, format="%.1f")
        cholesterol = st.number_input("Cholesterol (mg/dL)", min_value=0.0, step=0.1, format="%.1f")
        submitted = st.form_submit_button("Add Patient")

    if submitted:
        errors = validate_form(full_name, email, dob, glucose, haemoglobin, cholesterol)
        if errors:
            for error in errors:
                st.error(error)
            return

        remarks = ai_prediction.generate_health_remark(glucose, haemoglobin, cholesterol)
        try:
            database.add_patient(full_name.strip(), dob.isoformat(), email.strip(), glucose, haemoglobin, cholesterol, remarks)
            st.success("Patient record added successfully.")
            st.info("AI health remark generated and saved with the record.")
        except ValueError as value_error:
            st.error(str(value_error))
        except Exception as exception:
            st.error(f"Unable to save patient: {exception}")


def render_patient_records(patients):
    st.markdown("## Patient Records")
    if patients.empty:
        st.warning("No records available. Add a new patient first.")
        return
    st.dataframe(format_patient_table(patients), use_container_width=True)

    filter_name = st.text_input("Search by name or email")
    if filter_name:
        filtered = patients[patients["full_name"].str.contains(filter_name, case=False, na=False) | patients["email"].str.contains(filter_name, case=False, na=False)]
        st.dataframe(format_patient_table(filtered), use_container_width=True)


def render_update_delete(patients):
    st.markdown("## Update or Delete Records")
    if patients.empty:
        st.warning("No records to manage.")
        return

    selection = st.selectbox(
        "Select patient to manage",
        options=[f"{row['id']} - {row['full_name']}" for _, row in patients.iterrows()],
    )
    patient_id = int(selection.split(" - ")[0])
    record = database.get_patient(patient_id)
    if not record:
        st.error("Selected patient not found.")
        return

    with st.form("edit_form"):
        full_name = st.text_input("Full Name", value=record["full_name"])
        dob = st.date_input("Date of Birth", value=datetime.strptime(record["dob"], "%Y-%m-%d").date(), max_value=date.today())
        email = st.text_input("Email Address", value=record["email"])
        glucose = st.number_input("Glucose (mg/dL)", value=float(record["glucose"]), min_value=0.0, step=0.1, format="%.1f")
        haemoglobin = st.number_input("Haemoglobin (g/dL)", value=float(record["haemoglobin"]), min_value=0.0, step=0.1, format="%.1f")
        cholesterol = st.number_input("Cholesterol (mg/dL)", value=float(record["cholesterol"]), min_value=0.0, step=0.1, format="%.1f")
        update_button = st.form_submit_button("Update Patient")

    if update_button:
        errors = validate_form(full_name, email, dob, glucose, haemoglobin, cholesterol)
        if errors:
            for error in errors:
                st.error(error)
            return
        remarks = ai_prediction.generate_health_remark(glucose, haemoglobin, cholesterol)
        try:
            database.update_patient(patient_id, full_name.strip(), dob.isoformat(), email.strip(), glucose, haemoglobin, cholesterol, remarks)
            st.success("Patient record updated successfully.")
        except ValueError as value_error:
            st.error(str(value_error))
        except Exception as exception:
            st.error(f"Unable to update patient: {exception}")

    delete_confirmation = st.checkbox("I confirm deletion of this patient record.", key="confirm_delete")
    if delete_confirmation and st.button("Delete Patient", key="delete_button"):
        try:
            database.delete_patient(patient_id)
            st.success("Patient record deleted successfully.")
        except Exception as exception:
            st.error(f"Unable to delete patient: {exception}")


def render_ai_prediction():
    st.markdown("## AI Health Prediction")
    st.info("Enter blood values to generate a professional medical remark.")
    with st.form("prediction_form"):
        glucose = st.number_input("Glucose (mg/dL)", min_value=0.0, step=0.1, format="%.1f")
        haemoglobin = st.number_input("Haemoglobin (g/dL)", min_value=0.0, step=0.1, format="%.1f")
        cholesterol = st.number_input("Cholesterol (mg/dL)", min_value=0.0, step=0.1, format="%.1f")
        predict_button = st.form_submit_button("Generate Remark")

    if predict_button:
        errors = []
        for label, value in [("Glucose", glucose), ("Haemoglobin", haemoglobin), ("Cholesterol", cholesterol)]:
            if value is None or value < 0:
                errors.append(f"{label} must be a non-negative number.")
        if errors:
            for error in errors:
                st.error(error)
            return

        remark = ai_prediction.generate_health_remark(glucose, haemoglobin, cholesterol)
        st.success("Health remark generated successfully.")
        st.markdown("**AI Health Remark:**")
        st.write(remark)


def render_analytics(patients):
    st.markdown("## Analytics Dashboard")
    if patients.empty:
        st.warning("No patient data available for analytics.")
        return

    patients["risk_score"] = (
        patients["glucose"] / 126 + patients["cholesterol"] / 200 + (12.5 - patients["haemoglobin"]).clip(lower=0) / 5
    )
    fig_line = px.line(
        patients.sort_values("created_at"),
        x="created_at",
        y=["glucose", "haemoglobin", "cholesterol"],
        labels={"value": "Test Value", "variable": "Biomarker", "created_at": "Created At"},
        title="Patient Biomarker Trends",
        template="plotly_white",
    )
    fig_scatter = px.scatter(
        patients,
        x="glucose",
        y="cholesterol",
        color="haemoglobin",
        size_max=12,
        labels={"glucose": "Glucose", "cholesterol": "Cholesterol", "haemoglobin": "Haemoglobin"},
        title="Cholesterol vs Glucose",
        template="plotly_white",
    )

    st.plotly_chart(fig_line, use_container_width=True)
    st.plotly_chart(fig_scatter, use_container_width=True)

    lab_df = load_lab_dataset()
    if lab_df is not None:
        st.markdown("### Kaggle Laboratory Dataset Insights")
        st.markdown(f"Loaded **{len(lab_df)}** records from the Kaggle laboratory dataset.")
        st.dataframe(lab_df[["Gender", "Age", "Hemoglobin", "Glucose", "Cholesterol", "Disease"]].head(10), use_container_width=True)

        disease_counts = lab_df["Disease"].value_counts().reset_index(name="Count").rename(columns={"index": "Disease"})
        # Ensure the expected column names exist for plotting
        if list(disease_counts.columns)[:2] != ["Disease", "Count"]:
            disease_counts.columns = ["Disease", "Count"] + list(disease_counts.columns[2:])
        fig_bar = px.bar(
            disease_counts.head(12),
            x="Disease",
            y="Count",
            title="Top Diagnoses in Laboratory Dataset",
            template="plotly_white",
        )
        fig_scatter2 = px.scatter(
            lab_df,
            x="Glucose",
            y="Cholesterol",
            color="Hemoglobin",
            labels={"Glucose": "Glucose", "Cholesterol": "Cholesterol", "Hemoglobin": "Hemoglobin"},
            title="Kaggle Lab: Glucose vs Cholesterol",
            template="plotly_white",
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        st.plotly_chart(fig_scatter2, use_container_width=True)
    else:
        st.info("Optional Kaggle laboratory dataset not found at assets/laboratory__data.csv.")


def main():
    st.set_page_config(page_title="MIRA Health Prediction AI", page_icon="🩺", layout="wide")
    load_css()

    database.create_table()

    with st.sidebar:
        st.title("MIRA AI")
        st.markdown("Professional healthcare intelligence for patient risk management.")
        menu = st.selectbox(
            "Navigation",
            [
                "Dashboard",
                "Add Patient",
                "Patient Records",
                "Update/Delete Records",
                "AI Health Prediction",
                "Analytics Dashboard",
            ],
        )
        st.markdown("---")
        st.markdown("#### Resources")
        st.write("- Clean data workflows")
        st.write("- Rule-based health insights")
        if not ai_prediction.GROQ_API_KEY:
            st.warning("GROQ key not set. AI generation will use fallback remarks.")

    patients_data = database.get_patients()
    patients = pd.DataFrame(patients_data)

    if menu == "Dashboard":
        render_dashboard(patients)
    elif menu == "Add Patient":
        render_add_patient()
    elif menu == "Patient Records":
        render_patient_records(patients)
    elif menu == "Update/Delete Records":
        render_update_delete(patients)
    elif menu == "AI Health Prediction":
        render_ai_prediction()
    elif menu == "Analytics Dashboard":
        render_analytics(patients)

    st.markdown(
        "<div class='footer'>Built for healthcare assessments with Python, Streamlit, SQLite, and AI-assisted insights.</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
