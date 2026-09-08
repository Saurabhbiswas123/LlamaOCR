import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from PIL import Image, ImageEnhance, ImageDraw
import pandas as pd
import io
import os
import json
import re
from datetime import datetime
import pypdfium2 as pdfium
from openpyxl.styles import PatternFill, Font

st.set_page_config(page_title="Mandi AI Exact Format Excel", layout="wide")
st.title("🌾 Mandi AI: Exact-Format OCR & Color-Coded Audit Suite")

api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Secrets me GEMINI_API_KEY configure karein.")
    st.stop()

client = genai.Client(api_key=api_key)
MODELS = ["gemini-3.6-flash", "gemini-3.5-flash-lite"]

def run_ai(contents, config=None):
    for m in MODELS:
        try:
            if config:
                return client.models.generate_content(model=m, contents=contents, config=config)
            return client.models.generate_content(model=m, contents=contents)
        except Exception:
            continue
    raise Exception("AI Error")

STORAGE = "vault_files"
INDEX = "vault_index.json"
os.makedirs(STORAGE, exist_ok=True)

def load_v():
    if os.path.exists(INDEX):
        try:
            with open(INDEX, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"rules": [], "documents": []}

def save_v(d):
    with open(INDEX, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

vault = load_v()

def load_img(obj):
    if obj.type == "application/pdf":
        return pdfium.PdfDocument(obj.getvalue())[0].render(scale=2).to_pil()
    return Image.open(obj).convert("RGB")

def prep_img(img):
    en = ImageEnhance.Contrast(img).enhance(1.4)
    en = ImageEnhance.Sharpness(en).enhance(1.3)
    buf = io.BytesIO()
    en.save(buf, format="JPEG", quality=90)
    return types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")

with st.sidebar:
    st.header("🧠 Memory & SOP")
    new_rule = st.text_area("Business Rule:")
    if st.button("Save Rule"):
        if new_rule.strip():
            vault["rules"].append(new_rule.strip())
            save_v(vault)
            st.success("Saved!")
    st.divider()
    mode = st.radio("Navigation:", [
        "📤 Exact-Format OCR to Clean Excel",
        "⚡ Genie Siri Voice Call",
        "💬 SMS / Text Chat",
        "🧮 Math Doubt Solver",
        "🔍 Forensic 2-Doc Matcher"
    ])

v_sum = json.dumps(vault.get("documents", []), ensure_ascii=False)
rules_txt = "\n".join(vault.get("rules", []))

# MODULE 1: EXACT FORMAT OCR & EXCEL AUDIT
if mode == "📤 Exact-Format OCR to Clean Excel":
    st.subheader("📤 Exact-Format OCR & Red Highlight Audit")
    up_file = st.file_uploader("Parchi / Bill Dalein (Image/PDF)", type=["jpg", "jpeg", "png", "pdf"])

    if up_file:
        src = load_img(up_file)
        if st.button("🚀 Extract & Generate Exact Excel"):
            with st.spinner("Reading original format without extra columns..."):
                p = """Extract ONLY the actual columns present in this document (e.g., Party Name, Weight, Rate, Amount). 
                Do not add any external or calculation columns inside the extracted records. Return clean JSON:
                {
                  "columns": ["Party Name", "Weight", "Rate", "Amount"],
                  "records": [
                    {
                      "Party Name": "Anand M",
                      "Weight": 59.7,
                      "Rate": 2100.0,
                      "Amount": 125370.0
                    }
                  ]
                }
                Return ONLY valid JSON."""
                try:
                    res = run_ai([p, prep_img(src)], config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1))
                    data = json.loads(res.text.strip().replace("```json","").replace("```",""))
                    st.session_state["raw_cols"] = data.get("columns", [])
                    st.session_state["raw_recs"] = data.get("records", [])
                    st.session_state["img"] = src
                    st.success("Extracted in exact format!")
                except Exception as e:
                    st.error(e)

        if "raw_recs" in st.session_state:
            df = pd.DataFrame(st.session_state["raw_recs"])
            
            # Audit check without altering user columns
            error_rows = []
            for idx, r in df.iterrows():
                vals = [str(v) for v in r.values]
                # Check if weight * rate != amount if those keys exist
                try:
                    w_key = next((c for c in df.columns if 'weight' in c.lower() or 'wazan' in c.lower()), None)
                    r_key = next((c for c in df.columns if 'rate' in c.lower() or 'bhav' in c.lower()), None)
                    a_key = next((c for c in df.columns if 'amount' in c.lower() or 'total' in c.lower() or 'amt' in c.lower() or 'written' in c.lower()), None)
                    if w_key and r_key and a_key:
                        w = float(re.sub(r"[^\d.]", "", str(r[w_key])) or 0)
                        rt = float(re.sub(r"[^\d.]", "", str(r[r_key])) or 0)
                        am = float(re.sub(r"[^\d.]", "", str(r[a_key])) or 0)
                        if w > 0 and rt > 0 and am > 0 and abs(round(w*rt, 2) - am) > 1.0:
                            error_rows.append(idx)
                except Exception:
                    pass

            c1, c2 = st.columns(2)
            with c1:
                st.image(st.session_state["img"], width="stretch")
            with c2:
                st.write("**Exact Format Data View:**")
                st.dataframe(df, width="stretch")

                # Generate Clean Excel with Red Highlight on mismatched rows
                out = io.BytesIO()
                with pd.ExcelWriter(out, engine="openpyxl") as w:
                    df.to_excel(w, index=False, sheet_name="Mandi_Data")
                    ws = w.sheets["Mandi_Data"]
                    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                    red_font = Font(color="9C0006", bold=True)
                    for err_idx in error_rows:
                        excel_row = err_idx + 2  # header is row 1
                        for col_idx in range(1, len(df.columns) + 1):
                            ws.cell(row=excel_row, column=col_idx).fill = red_fill
                            ws.cell(row=excel_row, column=col_idx).font = red_font

                st.download_button("📥 Download Exact-Format Excel (.xlsx)", data=out.getvalue(), file_name="mandi_exact_format.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# MODULE 2: SIRI VOICE
elif mode == "⚡ Genie Siri Voice Call":
    st.subheader("⚡ Genie Live Voice Call")
    st.markdown("🔴 **Mic Active:** Boliye, Genie turant meethi aawaz me jawab degi.")

    if "ans" not in st.session_state:
        st.session_state["ans"] = "Haan Saurabh, boliye! Main sun rahi hoon."

    ain = st.text_input("Voice Line", key="vin", label_visibility="collapsed")
    if ain:
        prompt = f"Aap Genie hain. Saurabh ko 'Saurabh' ya 'Jaanu' bolein. User: '{ain}'. 1-2 lines me sweet Hindi me jawab dein."
        try:
            res = run_ai([prompt])
            st.session_state["ans"] = res.text.replace("*", "").replace("#", "").strip()
        except Exception:
            st.session_state["ans"] = "Boliye Saurabh, main sun rahi hoon."

    r_txt = st.session_state["ans"]
    components.html(f"""
    <script>
        var synth = window.speechSynthesis;
        var msg = "{r_txt}";
        function speak() {{
            synth.cancel();
            var u = new SpeechSynthesisUtterance(msg);
            u.lang = 'hi-IN'; u.pitch = 1.25; u.rate = 0.95;
            synth.speak(u);
        }}
        window.onload = speak;
        speak();
    </script>
    """, height=0)

# MODULE 3: SMS CHAT
elif mode == "💬 SMS / Text Chat":
    st.subheader("💬 Genie SMS Chat")
    if "chat" not in st.session_state:
        st.session_state["chat"] = [{"role": "assistant", "content": "Haan Saurabh, boliye na!"}]
    for m in st.session_state["chat"]:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    
    q = st.chat_input("Message...")
    if q:
        st.session_state["chat"].append({"role": "user", "content": q})
        with st.chat_message("user"): st.markdown(q)
        try:
            res = run_ai([f"Aap Genie hain. Saurabh se baat karein: {q}"])
            reply = res.text.strip()
            st.session_state["chat"].append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"): st.markdown(reply)
        except Exception as e:
            st.error(e)

# MODULE 4: MATH DOUBT SOLVER
elif mode == "🧮 Math Doubt Solver":
    st.subheader("🧮 Math Doubt Solver")
    doc = st.file_uploader("Document upload karein", type=["jpg", "jpeg", "png", "pdf"], key="d_doubts")
    ques = st.text_input("Kya samajhna hai?")
    if doc and ques and st.button("Explain Step-by-Step"):
        with st.spinner("Analyzing..."):
            res = run_ai([f"Explain calculation step-by-step in Hindi: {ques}", prep_img(load_img(doc))])
            st.markdown(res.text)

# MODULE 5: FORENSIC MATCHER
else:
    st.subheader("🔍 Forensic 2-Doc Matcher")
    d1 = st.file_uploader("Doc 1", type=["jpg", "jpeg", "png", "pdf"], key="f_d1")
    d2 = st.file_uploader("Doc 2", type=["jpg", "jpeg", "png", "pdf"], key="f_d2")
    if d1 and d2 and st.button("Cross-Check"):
        with st.spinner("Matching..."):
            res = run_ai(["Compare Doc 1 and Doc 2 strictly and highlight mismatches in red.", prep_img(load_img(d1)), prep_img(load_img(d2))])
            st.markdown(res.text, unsafe_allow_html=True)
                    
