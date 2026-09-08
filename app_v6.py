import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io
import time
import re
from openpyxl.styles import PatternFill, Font

st.set_page_config(page_title="Mandi OCR & Audit Matcher", layout="wide")
st.title("Mandi OCR: Strict Audit & Doubt Highlighting")

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
                    st.warning(f"API busy. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    raise Exception("API quota limit reached. Kripya 1 minute ruk kar dobara try karein.")
            else:
                raise e

app_mode = st.sidebar.radio("Mode Select Karein:", ["Single Document OCR", "2 Documents Cross-Check & Audit"])

# ----------------- MODE 1: Single Document OCR -----------------
if app_mode == "Single Document OCR":
    uploaded_file = st.sidebar.file_uploader("Photo ya PDF upload karein", type=["jpg", "jpeg", "png", "pdf"])
    
    if uploaded_file:
        if uploaded_file.type != "application/pdf":
            st.image(Image.open(uploaded_file), caption="Uploaded File")
        else:
            st.info(f"📄 Uploaded PDF: {uploaded_file.name}")

        if st.button("Extract Data with Zero-Assumption Audit"):
            with st.spinner("Handwriting & Calculations strictly audit ho rahi hain..."):
                prompt = """
                You are a senior forensic accountant auditing Indian Mandi receipts, kachhi parchi, bahi-khata, handwritten ledgers, and trade challans.
                Extract every transaction and ledger record into a structured Markdown table with 100% precision.

                CRITICAL FINANCIAL & NUMERICAL RULES:
                1. ZERO-ASSUMPTION POLICY: Never guess, approximate, extrapolate, or auto-complete any number, date, rate, bag count, weight, or name.
                2. DOUBT / AMBIGUITY TRIGGER:
                   - If any digit (e.g., distinguishing 0 vs 6, 1 vs 7, 3 vs 8), decimal point, or name is cut, faded, overwritten, smudged, or ambiguous by even 0.01%, DO NOT write a clean number.
                   - You MUST wrap that exact cell value inside this red highlight format:
                     `<span style='background-color: #ffcccc; color: #b30000; font-weight: bold; padding: 2px 5px; border-radius: 3px;'>🔴 [DOUBT: best_guess_or_unreadable]</span>`
                3. ARITHMETIC VERIFICATION:
                   - Always verify if: Quantity/Weight × Rate = Net Amount.
                   - If the handwritten net amount on the paper does NOT match the mathematical calculation, keep the written amount but append:
                     `<span style='background-color: #ffcccc; color: #b30000; font-weight: bold; padding: 2px 5px; border-radius: 3px;'>🔴 [CALC MISMATCH: written_val]</span>`
                4. CLEAN ENTRIES ONLY:
                   - Only enter numbers normally when they are 100% sharp, distinct, and legible.

                TABLE FORMAT:
                Return ONLY the structured Markdown Table with standard relevant columns:
                | S.No | Date | Name / Party Details | Item / Crop | Bags / Qty | Weight (Qntl/Kg) | Rate | Net Amount |

                Followed immediately by:
                ### 🔴 Flagged Items for Manual Verification
                - List every flagged row number, the field in doubt, and why it requires human inspection.
                """

                try:
                    res_text = call_gemini_with_retry([prompt, build_payload(uploaded_file)])
                    st.markdown(res_text, unsafe_allow_html=True)

                    # Extract table lines
                    lines = [line.strip() for line in res_text.strip().split("\n") if line.startswith("|") and line.endswith("|")]
                    if len(lines) > 2:
                        raw_data = [[c.strip() for c in line.split("|")[1:-1]] for line in lines]
                        headers = raw_data[0]
                        rows = raw_data[2:]

                        # Remove HTML tags for clean Excel viewing while keeping the 🔴 text
                        clean_rows = []
                        for row in rows:
                            clean_row = []
                            for cell in row:
                                clean_cell = re.sub(r'<[^>]*>', '', cell).strip()
                                clean_row.append(clean_cell)
                            clean_rows.append(clean_row)

                        df = pd.DataFrame(clean_rows, columns=headers)

                        # Write Excel and highlight cells in red
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine="openpyxl") as writer:
                            df.to_excel(writer, index=False, sheet_name="Mandi_Record")
                            ws = writer.sheets["Mandi_Record"]

                            red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                            red_font = Font(color="9C0006", bold=True)

                            for row_cells in ws.iter_rows(min_row=2, max_row=len(df)+1, min_col=1, max_col=len(headers)):
                                for cell in row_cells:
                                    val = str(cell.value or "")
                                    if "🔴" in val or "[DOUBT" in val or "MISMATCH" in val:
                                        cell.fill = red_fill
                                        cell.font = red_font

                        st.download_button(
                            label="📥 Download Excel Sheet with Red Highlighting (.xlsx)",
                            data=output.getvalue(),
                            file_name="verified_mandi_data.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                except Exception as ex:
                    st.error(f"Processing Error: {ex}")

# ----------------- MODE 2: 2 Documents Deep Cross-Check -----------------
else:
    st.subheader("🔍 Deep Cross-Verification (0.0001% Highlighted Difference Audit)")
    col1, col2 = st.columns(2)

    with col1:
        doc1 = st.file_uploader("First Document (Image/PDF)", type=["jpg", "jpeg", "png", "pdf"], key="doc1")
        if doc1 and doc1.type != "application/pdf":
            st.image(Image.open(doc1), caption="Document 1")
        elif doc1:
            st.info(f"📄 Doc 1: {doc1.name}")

    with col2:
        doc2 = st.file_uploader("Second Document (Image/PDF)", type=["jpg", "jpeg", "png", "pdf"], key="doc2")
        if doc2 and doc2.type != "application/pdf":
            st.image(Image.open(doc2), caption="Document 2")
        elif doc2:
            st.info(f"📄 Doc 2: {doc2.name}")

    if doc1 and doc2:
        if st.button("Compare & Highlight Differences"):
            with st.spinner("Dono documents ka micro-level audit chal raha hai..."):
                audit_prompt = """
                Compare Document 1 and Document 2 down to the smallest granular detail (0.0001% level).
                Highlight ANY mismatch or difference between both files using:
                `<span style='background-color: #ff4b4b; color: white; padding: 2px 5px; border-radius: 3px;'>🔴 VALUE (MISMATCH)</span>`.
                
                Highlight any unclear or faded number using:
                `<span style='background-color: #ff9800; color: white; padding: 2px 5px; border-radius: 3px;'>🟠 VALUE [UNCLEAR]</span>`.

                Provide:
                1. Final Verdict: MATCH or CRITICAL MISMATCH DETECTED
                2. Discrepancy Markdown Table
                3. Total Weight & Total Amount Reconciliation
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
                    
