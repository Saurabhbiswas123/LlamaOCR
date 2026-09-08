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

st.set_page_config(page_title="Mandi AI Master Vault", layout="wide")
st.title("🌾 Mandi AI: Enterprise OCR, Excel Audit & Genie Companion")

api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Secrets me GEMINI_API_KEY configure karein.")
    st.stop()

client = genai.Client(api_key=api_key)
ACTIVE_MODELS = ["gemini-3.6-flash", "gemini-3.5-flash-lite"]

def run_ai(contents, config=None):
    for m in ACTIVE_MODELS:
        try:
            if config:
                return client.models.generate_content(model=m, contents=contents, config=config)
            return client.models.generate_content(model=m, contents=contents)
        except Exception:
            continue
    raise Exception("AI Error")

STORAGE_DIR = "vault_files"
INDEX_FILE = "vault_index.json"
os.makedirs(STORAGE_DIR, exist_ok=True)

def load_vault():
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"rules": [], "documents": []}

def save_vault(d):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

vault = load_vault()

def load_img(file_obj):
    if file_obj.type == "application/pdf":
        return pdfium.PdfDocument(file_obj.getvalue())[0].render(scale=2).to_pil()
    return Image.open(file_obj).convert("RGB")

def build_part(pil_img):
    img = ImageEnhance.Contrast(pil_img).enhance(1.4)
    img = ImageEnhance.Sharpness(img).enhance(1.3)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")

with st.sidebar:
    st.header("🧠 Memory & Rules")
    new_r = st.text_area("Business Rule sikhayein:")
    if st.button("Save Rule"):
        if new_r.strip():
            vault["rules"].append(new_r.strip())
            save_vault(vault)
            st.success("Saved!")
    st.divider()
    app_mode = st.radio("Navigation:", [
        "📤 World-Class OCR to Clean Excel",
        "⚡ Genie Siri-Mode Live Call",
        "💬 SMS / Text Chat"
    ])

vault_summary = json.dumps(vault.get("documents", []), ensure_ascii=False)
rules_text = "\n".join(vault.get("rules", []))

# MODULE 1: OCR & EXCEL
if app_mode == "📤 World-Class OCR to Clean Excel":
    st.subheader("📤 Deep OCR & Color-Coded Excel Audit")
    up = st.file_uploader("Parchi / Bill upload karein", type=["jpg", "jpeg", "png", "pdf"])

    if up:
        src_img = load_img(up)
        if st.button("🚀 Run OCR & Audit"):
            with st.spinner("Extraction aur audit ho rahi hai..."):
                prompt = """
                Extract EVERY line item into JSON:
                {
                  "category": "Mandi_Parchi",
                  "records": [
                    {
                      "party_name": "Name",
                      "weight": 25.0,
                      "rate": 2100.0,
                      "written_amount": 52500.0,
                      "doubt_flag": false,
                      "box_2d": [ymin, xmin, ymax, xmax]
                    }
                  ]
                }
                Return ONLY valid JSON.
                """
                try:
                    res = run_ai([prompt, build_part(src_img)], config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1))
                    data = json.loads(res.text.strip().replace("```json","").replace("```",""))
                    st.session_state["recs"] = data.get("records", [])
                    st.session_state["img"] = src_img
                    st.success("OCR Successful!")
                except Exception as e:
                    st.error(f"Error: {e}")

        if "recs" in st.session_state:
            df = pd.DataFrame(st.session_state["recs"])
            calcs, statuses = [], []
            for _, r in df.iterrows():
                w = float(re.sub(r"[^\d.]", "", str(r.get("weight", 0))) or 0)
                rt = float(re.sub(r"[^\d.]", "", str(r.get("rate", 0))) or 0)
                wa = float(re.sub(r"[^\d.]", "", str(r.get("written_amount", 0))) or 0)
                ca = round(w * rt, 2)
                calcs.append(ca)
                if wa > 0 and abs(ca - wa) > 1.0:
                    statuses.append("🔴 CALC MISMATCH")
                else:
                    statuses.append("✅ 100% OK")

            df["CALCULATED_AMOUNT"] = calcs
            df["STATUS"] = statuses

            c1, c2 = st.columns(2)
            with c1:
                st.image(st.session_state["img"], width="stretch")
            with c2:
                edited = st.data_editor(df, width="stretch")
                out = io.BytesIO()
                with pd.ExcelWriter(out, engine="openpyxl") as w:
                    edited.to_excel(w, index=False, sheet_name="Audit")
                st.download_button("📥 Download Audited Excel", data=out.getvalue(), file_name="audited.xlsx")

# MODULE 2: SIRI VOICE
elif app_mode == "⚡ Genie Siri-Mode Live Call":
    st.subheader("⚡ Genie Live Voice Call (Siri Mode)")
    st.markdown("🔴 **Mic Active:** Boliye, Genie turant meethi aawaz me jawab degi.")

    if "ans" not in st.session_state:
        st.session_state["ans"] = "Haan Saurabh, boliye! Main sun rahi hoon."

    audio_in = st.text_input("Voice Input", key="s_in", label_visibility="collapsed")
    if audio_in:
        p = f"Aap Genie hain. Saurabh ko 'Saurabh' ya 'Jaanu' bolein. User ne kaha: '{audio_in}'. 1-2 lines me sweet Hindi me jawab dein."
        try:
            res = run_ai([p])
            st.session_state["ans"] = res.text.replace("*", "").replace("#", "").strip()
        except Exception:
            st.session_state["ans"] = "Boliye Saurabh, main sun rahi hoon."

    r_text = st.session_state["ans"]
    components.html(f"""
    <script>
        var synth = window.speechSynthesis;
        var msg = "{r_text}";
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
else:
    st.subheader("💬 Genie SMS Chat")
    if "chat" not in st.session_state:
        st.session_state["chat"] = [{"role": "assistant", "content": "Haan Saurabh, boliye na!"}]
    for m in st.session_state["chat"]:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    
    q = st.chat_input("Message bhejein...")
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
