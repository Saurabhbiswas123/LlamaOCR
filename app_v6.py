import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io
import time

st.set_page_config(page_title="Mandi OCR & Audit Matcher", layout="wide")
st.title("Mandi OCR: Table Extraction & Deep Audit Cross-Check")

api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Secrets me GEMINI_API_KEY configure karein.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-3.6-flash")

def build_payload(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}
    else:
        return Image.open(uploaded_file)

# Rate-limit safe API caller
def call_gemini_with_retry(payload_list, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = model.generate_content(payload_list)
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "ResourceExhausted" in error_str:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 8
                    st.warning(f"API busy/limit hit. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    raise Exception("Google API quota full ho gaya hai. Kripya 1 minute ruk kar dobara koshish karein.")
            else:
                raise e

app_mode = st.sidebar.radio("Mode Select Karein:", ["Single Document OCR", "2 Documents Cross-Check & Audit"])

# ----------------- MODE 1: Single Document OCR -----------------
if app_mode == "Single Document OCR":
    uploaded_file = st.sidebar.file_uploader("Document upload karein (Image/PDF)", type=["jpg", "jpeg", "png", "pdf"])
    
    if uploaded_file:
        if uploaded_file.type != "application/pdf":
            st.image(Image.open(uploaded_file), caption="Uploaded File")
        else:
            st.info(f"📄 Uploaded PDF: {uploaded_file.name}")

        if st.button("Extract Data to Table"):
            with st.spinner("Makka hisaab scan ho raha hai (Token-safe mode)..."):
                prompt = """
                Extract all handwritten and printed mandi ledger records from this document.
                Convert them into a clean, structured Markdown Table format.
                Columns typically needed: [S.No, Date, Farmer/Trader Name, Item (Makka/Maize), Weight/Bags, Rate, Net Amount].
                
                If any entry is doubtful, highlight it using:
                `<span style='background-color: #ff9800; color: white; padding: 2px 4px; border-radius: 3px;'>VALUE [UNCLEAR]</span>`.
                Only return the table and critical ledger summary.
                """
                try:
                    res_text = call_gemini_with_retry([prompt, build_payload(uploaded_file)])
                    st.markdown(res_text, unsafe_allow_html=True)

                    lines = [line.strip() for line in res_text.strip().split("\n") if "|" in line]
                    if len(lines) > 2:
                        raw_data = [[c.strip() for c in line.split("|")[1:-1]] for line in lines]
                        df = pd.DataFrame(raw_data[2:], columns=raw_data[0])
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine="openpyxl") as writer:
                            df.to_excel(writer, index=False)
                        st.download_button(
                            label="Download as Excel Sheet (.xlsx)",
                            data=output.getvalue(),
                            file_name="mandi_makka_data.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                except Exception as ex:
                    st.error(f"Execution Error: {ex}")

# ----------------- MODE 2: 2 Documents Deep Cross-Check -----------------
else:
    st.subheader("🔍 Deep Cross-Verification (0.0001% Highlighted Difference Audit)")
    col1, col2 = st.columns(2)

    with col1:
        doc1 = st.file_uploader("Upload First Document", type=["jpg", "jpeg", "png", "pdf"], key="doc1")
        if doc1 and doc1.type != "application/pdf":
            st.image(Image.open(doc1), caption="Document 1")
        elif doc1:
            st.info(f"📄 Doc 1: {doc1.name}")

    with col2:
        doc2 = st.file_uploader("Upload Second Document", type=["jpg", "jpeg", "png", "pdf"], key="doc2")
        if doc2 and doc2.type != "application/pdf":
            st.image(Image.open(doc2), caption="Document 2")
        elif doc2:
            st.info(f"📄 Doc 2: {doc2.name}")

    if doc1 and doc2:
        if st.button("Compare & Highlight Differences"):
            with st.spinner("Dono documents ka precision audit chal raha hai..."):
                audit_prompt = """
                Compare Document 1 and Document 2 down to the smallest detail (even 0.0001% numerical/weight differences).
                Wrap mismatched items in:
                `<span style='background-color: #ff4b4b; color: white; padding: 2px 5px; border-radius: 3px;'>VALUE (MISMATCH)</span>`.
                Wrap unclear values in:
                `<span style='background-color: #ff9800; color: white; padding: 2px 5px; border-radius: 3px;'>VALUE [UNCLEAR]</span>`.

                Output structure:
                1. Verdict (MATCH or DISCREPANCY DETECTED)
                2. Markdown Discrepancies Table
                3. Total Weight & Amount Reconciliation
                """
                try:
                    res_text = call_gemini_with_retry([
                        audit_prompt,
                        "Doc 1:", build_payload(doc1),
                        "Doc 2:", build_payload(doc2)
                    ])
                    st.markdown(res_text, unsafe_allow_html=True)
                except Exception as ex:
                    st.error(f"Audit Error: {ex}")
