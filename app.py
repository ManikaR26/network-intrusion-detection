from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from config import DEMO_DIR, REPORTS_DIR
from src.common import load_json
from src.inference import analyze_dataframe

st.set_page_config(page_title="Network Intrusion Detection", page_icon="🛡️", layout="wide")

st.title("🛡️ Network Intrusion Detection & Anomaly Monitoring")
st.caption("XGBoost classifies known traffic patterns; a PyTorch autoencoder flags unusual behavior.")


def run_analysis(df):
    try:
        with st.spinner("Analyzing network-flow records..."):
            results, info = analyze_dataframe(df)
        return results, info
    except Exception as exc:
        st.error(str(exc))
        return None, None


def show_results(results, info):
    total = len(results)
    attacks = int((results["Prediction"].str.upper() != "BENIGN").sum())
    anomalies = int(results["Autoencoder Anomaly"].sum())
    high = int((results["Risk"] == "HIGH").sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Records analyzed", f"{total:,}")
    c2.metric("Known attacks", f"{attacks:,}")
    c3.metric("Autoencoder anomalies", f"{anomalies:,}")
    c4.metric("High-risk records", f"{high:,}")

    left, right = st.columns(2)
    with left:
        counts = results["Prediction"].value_counts().rename_axis("Traffic type").reset_index(name="Count")
        fig = px.bar(counts, x="Traffic type", y="Count", title="Predicted traffic classes")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        risk_counts = results["Risk"].value_counts().rename_axis("Risk").reset_index(name="Count")
        fig2 = px.pie(risk_counts, names="Risk", values="Count", title="Risk distribution")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Detection results")
    display = results.copy()
    display["Confidence"] = (display["Confidence"] * 100).round(2).astype(str) + "%"
    display["Anomaly Score"] = display["Anomaly Score"].round(5)
    st.dataframe(display, use_container_width=True, height=360)

    if info.get("missing_features"):
        st.info(f"{len(info['missing_features'])} training feature(s) were missing from the upload and were imputed.")

    csv = results.to_csv(index=False).encode("utf-8")
    st.download_button("Download prediction report", csv, "intrusion_detection_results.csv", "text/csv")


tab1, tab2, tab3 = st.tabs(["Analyze traffic", "Model summary", "How it works"])

with tab1:
    st.write("Upload a network-flow CSV produced with the same features used to train the model.")
    uploaded = st.file_uploader("Choose CSV", type=["csv"])
    demo_path = DEMO_DIR / "upload_sample.csv"
    col1, col2 = st.columns([1, 2])
    with col1:
        demo_clicked = st.button("Run bundled demo sample", disabled=not demo_path.exists())
    if uploaded is not None:
        df = pd.read_csv(uploaded, low_memory=False)
        results, info = run_analysis(df)
        if results is not None:
            show_results(results, info)
    elif demo_clicked:
        df = pd.read_csv(demo_path, low_memory=False)
        results, info = run_analysis(df)
        if results is not None:
            show_results(results, info)

with tab2:
    metrics_path = REPORTS_DIR / "training_metrics.json"
    if metrics_path.exists():
        m = load_json(metrics_path)
        st.json(m)
        st.caption("Demo metrics are only a pipeline check. Train on CIC-IDS2017 before using metrics on a resume/report.")
    else:
        st.warning("Training metrics not found. Run the training script first.")

with tab3:
    st.markdown("""
    **1. XGBoost classifier:** predicts a known class such as BENIGN, DDoS, DoS, PortScan or BruteForce.  
    **2. Autoencoder:** learns BENIGN traffic patterns and calculates reconstruction error for each new record.  
    **3. Risk logic:** known attacks are high/medium risk; BENIGN records with unusual reconstruction error are flagged as anomalies.  
    **4. Dashboard:** summarizes predictions and lets you export the result report.
    """)
