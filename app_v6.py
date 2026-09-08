import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io

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
            with st.spinner("Data extraction ongoing..."):
                prompt = """
                Extract all handwritten and printed records from this document.
                Convert them into a structured Markdown Table format.
                Columns: [S.No, Date, Name/Details, Weight/Qty, Rate, Total Amount].
                
                CRITICAL INSTRUCTION:
                If any digit, word, or calculation is blurry, overwritten, or doubtful, wrap that specific text inside:
                `<span style='background-color: #ffbf00; color: black; font-weight: bold; padding: 2px 5px; border-radius: 3px;'>TEXT [DOUBT]</span>`.
                Only return the table and a short note on doubtful entries.
                """
                payload = [prompt, build_payload(uploaded_file)]
                response = model.generate_content(payload)
                st.markdown(response.text, unsafe_allow_html=True)

                try:
                    lines = [line.strip() for line in response.text.strip().split("\n") if "|" in line]
                    if len(lines) > 2:
                        raw_data = [[c.strip() for c in line.split("|")[1:-1]] for line in lines]
                        df = pd.DataFrame(raw_data[2:], columns=raw_data[0])
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine="openpyxl") as writer:
                            df.to_excel(writer, index=False)
                        st.download_button(
                            label="Download as Excel Sheet (.xlsx)",
                            data=output.getvalue(),
                            file_name="mandi_ledger_data.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                except Exception:
                    pass

# ----------------- MODE 2: 2 Documents Deep Cross-Check -----------------
else:
    st.subheader("🔍 Deep Cross-Verification (0.0001% Highlighted Difference Audit)")
    col1, col2 = st.columns(2)

    with col1:
        doc1 = st.file_uploader("Upload First Document (Parchi / Ledger)", type=["jpg", "jpeg", "png", "pdf"], key="doc1")
        if doc1 and doc1.type != "application/pdf":
            st.image(Image.open(doc1), caption="Document 1")
        elif doc1:
            st.info(f"📄 Doc 1: {doc1.name}")

    with col2:
        doc2 = st.file_uploader("Upload Second Document (Challan / Bill)", type=["jpg", "jpeg", "png", "pdf"], key="doc2")
        if doc2 and doc2.type != "application/pdf":
            st.image(Image.open(doc2), caption="Document 2")
        elif doc2:
            st.info(f"📄 Doc 2: {doc2.name}")

    if doc1 and doc2:
        if st.button("Compare & Highlight Differences"):
            with st.spinner("Dono documents ko 0.0001% precision par audit aur highlight kiya ja raha hai..."):
                audit_prompt = """
                You are a forensic auditor for Indian Mandi receipts, kachhi parchi, bills, and ledger books.
                Compare Document 1 and Document 2 down to the smallest granular detail (including 0.0001% numerical deviations, slight spelling differences, line omissions, date mismatch, or rate mismatches).

                HIGHLIGHTING INSTRUCTIONS:
                1. Whenever you find ANY difference, discrepancy, or mismatch between Doc 1 and Doc 2, wrap the mismatched text in BOTH columns with:
                   `<span style='background-color: #ff4b4b; color: white; font-weight: bold; padding: 2px 6px; border-radius: 4px;'>VALUE (MISMATCH)</span>`.
                2. If an entry is doubtful or difficult to read clearly, wrap it with:
                   `<span style='background-color: #ff9800; color: white; font-weight: bold; padding: 2px 6px; border-radius: 4px;'>VALUE [UNCLEAR]</span>`.

                Structure the final audit report strictly as follows:

                ### 1. Audit Verdict
                - State **MATCH CONFIRMED** in green or **CRITICAL DIFFERENCES DETECTED** in bold red.

                ### 2. Discrepancies & Doubtful Items Table
                Provide a Markdown table with colored highlights:
                | Line / Item | Doc 1 Record | Doc 2 Record | Variance / Nature of Doubt |
                |---|---|---|---|
                *(If 100% identical without doubt, write "No differences or doubtful entries detected.")*

                ### 3. Quantitative & Monetary Verification
                - **Doc 1 Total Weight vs Doc 2 Total Weight**: (highlight difference if any)
                - **Doc 1 Total Amount vs Doc 2 Total Amount**: (highlight difference if any)
                - **Math Calculation Accuracy**: Check if Rate x Weight = Total Amount holds true on both papers.

                ### 4. Direct Action Points
                List every exact field that the human accountant needs to double check immediately.
                """

                payload1 = build_payload(doc1)
                payload2 = build_payload(doc2)

                try:
                    response = model.generate_content([
                        audit_prompt,
                        "Document 1:", payload1,
                        "Document 2:", payload2
                    ])
                    # Enable unsafe_allow_html to render red/yellow color tags
                    st.markdown(response.text, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Audit failed: {e}")
                    
