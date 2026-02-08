import streamlit as st
import os
import re
import base64
import requests
from groq import Groq
import plotly.graph_objects as go
import time
from fpdf import FPDF
import pandas as pd
from googlesearch import search

# ================= 1. PAGE CONFIG & STYLING =================
st.set_page_config(
    page_title="FraudLens AI Security Platform",
    page_icon="🔍",
    layout="wide"
)

st.markdown("""
<style>
    .main { background-color: #f4f7f9; }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        background-color: #ff4444;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ================= 2. API & ENV SETUP =================
GROQ_API_KEY = os.getenv("API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

# ================= 3. SHARED HELPERS =================
def defang(text):
    return text.replace("http", "hxxp").replace(".", "[.]")

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.read()).decode("utf-8")

def draw_gauge(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': "Risk Level", 'font': {'size': 18}},
        gauge={
            'axis': {'range': [0, 10]},
            'steps': [
                {'range': [0, 3], 'color': "#00cc44"},
                {'range': [3, 7], 'color': "#ffcc00"},
                {'range': [7, 10], 'color': "#ff4444"}
            ],
            'bar': {'color': "black"}
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def fetch_online_content(query, num_results=2):
    try:
        search_query = f"{query} MFSA cybersecurity compliance trading risk"
        results = search(search_query, num_results=num_results, advanced=True)
        snippets = [f"Source: {res.title}\nContent: {res.description}" for res in results]
        return "\n\n".join(snippets) if snippets else "No direct regulatory data found."
    except:
        return "Regulatory search unavailable at the moment."

def groq_chat_with_retry(model, messages, max_retries=3):
    for _ in range(max_retries):
        try:
            completion = groq_client.chat.completions.create(model=model, messages=messages)
            return completion.choices[0].message.content
        except: time.sleep(1)
    return "The reasoning engine is currently over capacity."

# ================= 4. PERSISTENT SESSION STATE =================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_chat" not in st.session_state:
    st.session_state.show_chat = False

# ================= 5. SIDEBAR (GRC BOT ONLY) =================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1063/1063376.png", width=100)
    st.title("🛡️ FraudLens Control")
    st.info("Module: Fraud & Scam Detection (Active)")
    
    st.divider()
    
    # Floating Toggle Button logic
    btn_label = "❌ Close GRC Assistant" if st.session_state.show_chat else "💬 Open GRC Assistant"
    if st.button(btn_label):
        st.session_state.show_chat = not st.session_state.show_chat
        st.rerun()

    if st.session_state.show_chat:
        st.markdown("---")
        st.subheader("🤖 GRC Compliance Bot")
        chat_container = st.container(height=400)
        with chat_container:
            for m in st.session_state.messages:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

        if chat_input := st.chat_input("Ask about MFSA rules..."):
            st.session_state.messages.append({"role": "user", "content": chat_input})
            with chat_container:
                with st.chat_message("user"): st.markdown(chat_input)
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing Compliance..."):
                        context = fetch_online_content(chat_input)
                        full_prompt = f"Regulatory Context: {context}\n\nUser: {chat_input}"
                        res = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": "You are a professional GRC expert for Deriv. Refer to MFSA and Cybersecurity standards."},
                                {"role": "user", "content": full_prompt}
                            ]
                        ).choices[0].message.content
                        st.markdown(res)
                        st.session_state.messages.append({"role": "assistant", "content": res})
                        st.rerun()

        if st.button("🗑️ Clear History"):
            st.session_state.messages = []
            st.rerun()

# ================= 6. MAIN CONTENT AREA =================
st.title("🔍 FraudLens AI Security Platform")
st.caption("Active Forensics + Regulatory Intelligence")

st.header("🕵️ Fraud & Scam Analysis")
tab1, tab2, tab3, tab4 = st.tabs(["📧 Email Scan", "💬 Chat Audit", "📸 Document Forensics", "🤖 AI vs AI Defense"])

with tab1:
    email_text = st.text_area("Paste email/link for analysis", height=150)
    if st.button("Analyze Email"):
        if email_text:
            with st.spinner("Scanning for Phishing..."):
                res = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"Analyze for fraud and return Risk Score (0-10) and reasoning, and if the risk level is above 5 then map it to a relevant MITRE ATT&CK ID: {email_text}"}]
                ).choices[0].message.content
                score_match = re.search(r"\d+", res)
                score = int(score_match.group()) if score_match else 5
                c1, c2 = st.columns(2)
                with c1: st.plotly_chart(draw_gauge(score), use_container_width=True)
                with c2: st.markdown(res)
                st.code(defang(email_text))

with tab2:
    chat_text = st.text_area("Paste chat transcript (P2P/Internal)", height=150)
    if st.button("Run Audit"):
        if chat_text:
            with st.spinner("Analyzing Social Engineering..."):
                res = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"Audit for off-platform luring and trust abuse: {chat_text}"}]
                ).choices[0].message.content
                st.markdown(res)

with tab3:
    img_file = st.file_uploader("Upload Receipt/Document", type=["png", "jpg", "jpeg"])
    if img_file:
        st.image(img_file, width=300)
        if st.button("Start Forensic Audit"):
            with st.spinner("Pixel Forensic Analysis..."):
                b64 = encode_image(img_file)
                res = groq_chat_with_retry(
                    model="llama-3.2-11b-vision-preview",
                    messages=[{"role": "user", "content": [{"type": "text", "text": "Audit for tampering/Photoshop."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}]
                )
                st.markdown(res)

with tab4:
    ai_txt = st.text_area("Input message to check for AI generation", height=150)
    if st.button("Detect Machine Logic"):
        with st.spinner("Running Perplexity Check..."):
            res = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"Is this AI generated? Provide probability %: {ai_txt}"}]
            ).choices[0].message.content
            st.markdown(res)