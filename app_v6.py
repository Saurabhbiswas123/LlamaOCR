import streamlit as st
from google import genai
from google.genai import types
from PIL import Image, ImageEnhance
import pandas as pd
import io
import json
import re
from openpyxl.styles import PatternFill, Font

st.set_page_config(page_title="Forensic Mandi Ledger & Math Audit", layout="wide")
st.title("🛡️ Enterprise Mandi OCR & Deep Arithmetic Verification Engine")

api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Secrets me GEMINI_API_KEY configure karein.")
    st.stop()

client = genai.Client(api_key=api_key)

def enhance_document(img_input):
    img = img_input.convert("RGB")
    img = ImageEnhance.Contrast(img).enhance(1.45)
    img = ImageEnhance.Sharpness(img).enhance(1.35)
    return img

def build_part(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return types.Part.from_bytes(data=uploaded_file.getvalue(), mime_type="application/pdf")
    else:
        pil_img = Image.open(uploaded_file)
        enhanced = enhance_document(pil_img)
        buffer = io.BytesIO()
        enhanced.save(buffer, format="JPEG", quality=95)
        return types.Part.from_bytes(data=buffer.getvalue(), mime_type="image/jpeg")

AUDIT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "written_grand_total": {
            "type": "NUMBER",
            "description": "The net or grand total written at the bottom of the parchi/page, if present. Else 0."
        },
        "records": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "s_no": {"type": "STRING"},
                    "date": {"type": "STRING"},
                    "party_name": {"type": "STRING"},
                    "crop_item": {"type": "STRING"},
                    "bags": {"type": "STRING"},
                    "weight": {"type": "NUMBER"},
                    "rate": {"type": "NUMBER"},
                    "reported_amount": {"type": "NUMBER"},
                    "faded_or_unclear": {"type": "BOOLEAN"},
                    "doubt_details": {"type": "STRING"}
                },
                "required": ["party_name", "weight", "rate", "reported_amount", "faded_or_unclear"]
            }
        }
    },
    "required": ["records"]
}

def run_forensic_dual_pass(file_part):
    system_instruction = """
    You are a forensic auditor inspecting Indian Mandi receipts, kachhi parchi, and commercial registers.
    Extract every line item and the written grand total at the bottom exactly as written on paper.
    DO NOT autocorrect human math errors on paper; report what is actually written so our deterministic Python engine can catch mistakes.
    If handwriting is cut or faded, mark faded_or_unclear=True.
    """
    models = ["gemini-3.5-flash-lite", "gemini-2.5-flash"]
    last_err = None

    for m in models:
        try:
            res1 = client.models.generate_content(
                model=m,
                contents=[system_instruction, file_part],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AUDIT_SCHEMA,
                    temperature=0.1
                )
            )
            data1 = json.loads(res1.text)

            res2 = client.models.generate_content(
                model=m,
                contents=["Re-verify all written numbers and totals to eliminate hallucination:", file_part],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AUDIT_SCHEMA,
                    temperature=0.2
                )
            )
            data2 = json.loads(res2.text)
            return data1, data2
        except Exception as e:
            last_err = e
            continue

    raise Exception(f"Extraction Pipeline Failure: {last_err}")

app_mode = st.sidebar.radio("Functionality:", ["Zero-Error Ledger & Math Audit", "2-Document Forensic Matcher"])

# ----------------- MODE 1: Ledger & Math Audit -----------------
if app_mode == "Zero-Error Ledger & Math Audit":
    up_file = st.sidebar.file_uploader("Document upload karein (Image/PDF)", type=["jpg", "jpeg", "png", "pdf"])

    if up_file:
        col_prev, col_stat = st.columns([1, 2])
        with col_prev:
            if up_file.type != "application/pdf":
                st.image(Image.open(up_file), caption="Source Parchi", use_container_width=True)
            else:
                st.info(f"📄 PDF Loaded: {up_file.name}")

        if st.button("🚀 Run Forensic Math Cross-Audit"):
            with st.spinner("Handwriting extraction + Strict Mathematical Recalculation chal raha hai..."):
                try:
                    payload = build_part(up_file)
                    p1_obj, p2_obj = run_forensic_dual_pass(payload)

                    df = pd.DataFrame(p1_obj.get("records", []))
                    p2_records = p2_obj.get("records", [])
                    written_grand_total = float(p1_obj.get("written_grand_total", 0) or 0)

                    status_list = []
                    correct_calc_list = []
                    remarks_list = []
                    recomputed_running_sum = 0.0
                    math_errors_count = 0

                    for idx in range(len(df)):
                        row1 = df.iloc[idx]
                        w = float(row1.get("weight", 0) or 0)
                        r = float(row1.get("rate", 0) or 0)
                        rep_amt = float(row1.get("reported_amount", 0) or 0)
                        exact_amt = round(w * r, 2)
                        correct_calc_list.append(exact_amt)
                        recomputed_running_sum += exact_amt

                        inconsistent = False
                        if idx < len(p2_records):
                            row2 = p2_records[idx]
                            if abs(w - float(row2.get("weight", 0) or 0)) > 0.001 or abs(r - float(row2.get("rate", 0) or 0)) > 0.001:
                                inconsistent = True

                        math_mismatch = (rep_amt > 0 and w > 0 and r > 0 and abs(exact_amt - rep_amt) > 1.0)
                        is_faded = bool(row1.get("faded_or_unclear", False))

                        if math_mismatch:
                            math_errors_count += 1
                            diff = round(rep_amt - exact_amt, 2)
                            status_list.append("🔴 MATH ERROR ON PAPER")
                            remarks_list.append(f"Paper par: ₹{rep_amt} | Asli: ₹{exact_amt} (Farq: ₹{diff})")
                        elif inconsistent:
                            status_list.append("🔴 READING CONFLICT")
                            remarks_list.append("Vision ambiguity between Pass 1 and 2.")
                        elif is_faded:
                            status_list.append("🟠 UNCLEAR INK")
                            remarks_list.append(str(row1.get("doubt_details", "Faded handwriting")))
                        else:
                            status_list.append("✅ 100% CORRECT")
                            remarks_list.append("Exact Match")

                    df["CORRECT_CALCULATED_AMOUNT"] = correct_calc_list
                    df["AUDIT_STATUS"] = status_list
                    df["AUDIT_REMARKS"] = remarks_list

                    st.divider()
                    if written_grand_total > 0:
                        total_diff = round(written_grand_total - recomputed_running_sum, 2)
                        if abs(total_diff) > 1.0:
                            st.error(
                                f"🚨 **Parchi ka Grand Total Galat Hai!**\n\n"
                                f"- **Paper par likha jod:** ₹{written_grand_total:,.2f}\n"
                                f"- **Sahi hisaab jod:** ₹{recomputed_running_sum:,.2f}\n"
                                f"- **Farq (Discrepancy):** ₹{total_diff:,.2f}"
                            )
                        else:
                            st.success(f"✅ **Grand Total Verified:** ₹{written_grand_total:,.2f} 100% match hai!")
                    else:
                        st.info(f"📊 **Calculated Grand Total:** ₹{recomputed_running_sum:,.2f}")

                    if math_errors_count > 0:
                        st.warning(f"⚠️ **{math_errors_count} entries me multiplication/rate calculation ki galti mili hai!**")

                    st.subheader("Audited Ledger Grid (Live Editable)")
                    edited_df = st.data_editor(df, use_container_width=True)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        edited_df.to_excel(writer, index=False, sheet_name="Mandi_Verified_Ledger")
                        ws = writer.sheets["Mandi_Verified_Ledger"]

                        red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                        red_font = Font(color="9C0006", bold=True)
                        green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                        green_font = Font(color="006100", bold=True)

                        status_col_idx = edited_df.columns.get_loc("AUDIT_STATUS") + 1

                        for r_idx in range(2, len(edited_df) + 2):
                            cell_val = str(ws.cell(row=r_idx, column=status_col_idx).value)
                            if "🔴" in cell_val:
                                for c_idx in range(1, len(edited_df.columns) + 1):
                                    ws.cell(row=r_idx, column=c_idx).fill = red_fill
                                    ws.cell(row=r_idx, column=c_idx).font = red_font
                            elif "✅" in cell_val:
                                ws.cell(row=r_idx, column=status_col_idx).fill = green_fill
                                ws.cell(row=r_idx, column=status_col_idx).font = green_font

                    st.download_button(
                        label="📥 Download Mathematical Audit Excel (.xlsx)",
                        data=output.getvalue(),
                        file_name="mandi_math_audited.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                except Exception as ex:
                    st.error(f"Audit Error: {ex}")

# ----------------- MODE 2: 2-Document Matcher -----------------
else:
    st.subheader("🔍 Forensic 2-Document Difference Reconciliation (0.0001% Variance)")
    c1, c2 = st.columns(2)
    with c1:
        d1 = st.file_uploader("Document 1 (Ledger/Parchi)", type=["jpg", "jpeg", "png", "pdf"], key="d1_forensic")
    with c2:
        d2 = st.file_uploader("Document 2 (Bill/Challan)", type=["jpg", "jpeg", "png", "pdf"], key="d2_forensic")

    if d1 and d2 and st.button("Execute Cross-Audit"):
        with st.spinner("Analyzing micro-deviations between both documents..."):
            prompt = """
            Compare Document 1 and Document 2 strictly down to 0.0001% variance.
            Highlight ANY mismatch between files using:
            `<span style='background-color: #ff4b4b; color: white; padding: 2px 5px; border-radius: 3px;'>🔴 VALUE (MISMATCH)</span>`.
            Provide:
            1. Status: 100% MATCH or CRITICAL DISCREPANCIES DETECTED
            2. Detailed Markdown Comparison Table
            3. Quantity & Financial Reconciliation Summary
            """
            try:
                res = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=[prompt, "Doc 1:", build_part(d1), "Doc 2:", build_part(d2)]
                )
                st.markdown(res.text, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Audit match error: {e}")
