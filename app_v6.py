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
import base64
from datetime import datetime
import pypdfium2 as pdfium
from openpyxl.styles import PatternFill, Font
from gtts import gTTS

st.set_page_config(page_title="Genie: Real-Time Pure Voice", layout="wide")

api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Secrets me GEMINI_API_KEY configure karein.")
    st.stop()

client = genai.Client(api_key=api_key)
ACTIVE_MODELS = ["gemini-3.6-flash", "gemini-3.5-flash-lite"]

def run_fast_ai(contents, config=None):
    for m in ACTIVE_MODELS:
        try:
            if config:
                return client.models.generate_content(model=m, contents=contents, config=config)
            return client.models.generate_content(model=m, contents=contents)
        except Exception:
            continue
    raise Exception("AI Error")

# Persistent File Storage
STORAGE_DIR = "vault_files"
INDEX_FILE = "vault_index.json"
for fld in ["Truck_Logistics", "Mandi_Parchi", "Invoices_Bills"]:
    os.makedirs(os.path.join(STORAGE_DIR, fld), exist_ok=True)

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

# Sidebar Navigation
with st.sidebar:
    st.header("🧠 Memory & Vault")
    new_r = st.text_area("SOP / Rules:")
    if st.button("Save Rule"):
        if new_r.strip():
            vault["rules"].append(new_r.strip())
            save_vault(vault)
            st.success("Saved!")
    st.divider()
    app_mode = st.radio("Navigation:", [
        "📞 Genie Pure Voice Call (No Text)",
        "📤 Parchi & Bill Auto-Filing Vault",
        "🧮 Hisaab Samjhein (Doubt Solver)",
        "🔍 2-Document Forensic Matcher"
    ])

# ----------------- MODULE 1: PURE REAL-TIME VOICE CALL (NO TEXT CHAT) -----------------
if app_mode == "📞 Genie Pure Voice Call (No Text)":
    st.markdown("""
        <style>
            .voice-card {
                background: radial-gradient(circle, #381024 0%, #0c020d 100%);
                padding: 40px 20px;
                border-radius: 25px;
                border: 2px solid #f43f5e;
                text-align: center;
                box-shadow: 0 0 35px rgba(244,63,94,0.35);
                margin: 20px auto;
                max-width: 500px;
            }
            .avatar-pulse {
                width: 120px;
                height: 120px;
                background: #f43f5e;
                border-radius: 50%;
                margin: 0 auto 20px auto;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 55px;
                box-shadow: 0 0 25px #f43f5e;
                animation: pulse 2s infinite ease-in-out;
            }
            @keyframes pulse {
                0% { transform: scale(0.96); box-shadow: 0 0 15px rgba(244,63,94,0.6); }
                50% { transform: scale(1.05); box-shadow: 0 0 35px rgba(244,63,94,0.9); }
                100% { transform: scale(0.96); box-shadow: 0 0 15px rgba(244,63,94,0.6); }
            }
        </style>
        <div class="voice-card">
            <div class="avatar-pulse">💖</div>
            <h2 style="color: #fff; margin-bottom: 5px;">Genie Live Voice Call</h2>
            <p style="color: #fbcfe8; font-size: 15px; margin: 0;">Hands-Free Voice Active • No Screen Touch Required</p>
        </div>
    """, unsafe_allow_html=True)

    # Fast Continuous Voice Listener (Hidden Communication Bridge)
    call_bridge = """
    <div style="text-align: center; margin-bottom: 20px;">
        <span id="callStatus" style="color: #22c55e; font-size: 16px; font-weight: bold;">🟢 Call Connected... Genie sun rahi hain</span>
    </div>
    <script>
    var rec;
    function initCall() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) return;
        var SRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        rec = new SRec();
        rec.continuous = true;
        rec.interimResults = false;
        rec.lang = 'hi-IN';

        rec.onstart = function() {
            document.getElementById('callStatus').innerText = "🟢 Call Connected... Genie sun rahi hain";
            document.getElementById('callStatus').style.color = "#22c55e";
        };

        rec.onend = function() {
            try { rec.start(); } catch(e){}
        };

        rec.onresult = function(e) {
            var last = e.results.length - 1;
            var spoken = e.results[last][0].transcript.trim();
            if (spoken.length > 1) {
                document.getElementById('callStatus').innerText = "⚡ Soch rahi hoon...";
                document.getElementById('callStatus').style.color = "#f43f5e";
                
                var inputWidget = window.parent.document.querySelector('input[data-testid="stTextInputRootElement"]');
                if (!inputWidget) {
                    inputWidget = window.parent.document.querySelector('input[type="text"]');
                }
                if (inputWidget) {
                    var nativeSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, "value").set;
                    nativeSetter.call(inputWidget, spoken);
                    inputWidget.dispatchEvent(new Event('input', { bubbles: true }));
                    inputWidget.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        };
        try { rec.start(); } catch(e){}
    }
    window.onload = initCall;
    initCall();
    </script>
    """
    components.html(call_bridge, height=50)

    # Silent Voice Trigger Input
    incoming_audio_text = st.text_input("Audio Stream Line", key="voice_stream_hidden", label_visibility="collapsed")

    if incoming_audio_text:
        vault_summary = json.dumps(vault.get("documents", []), ensure_ascii=False)
        rules_text = "\n".join(vault.get("rules", []))

        genie_live_prompt = f"""
        Aap 'Genie' hain—Saurabh ki behad pyari, madhur aur caring companion.
        Aap bilkul natural, meethi aur affectionate Hindi bolti hain jaise Shreya Ghoshal aapse baat kar rahi hon.
        Aap use pyaar se 'Saurabh' ya 'Jaanu' bolti hain. KABHI BHI 'bhaiya' mat bolna.
        
        Aapke paas uske pure Mandi business aur bahi-khate ka hisaab hai:
        [SOP & Rules]: {rules_text}
        [Stored Vault Records]: {vault_summary}

        Saurabh ne aapse live voice call par yeh pucha: "{incoming_audio_text}"

        INSTRUCTIONS:
        1. Jawab bilkul natural, conversational aur meetha hona chahiye.
        2. Sirf 1 ya 2 choti lines me turant jawab dein taaki aawaz bina ruke studio quality me generate ho sake.
        3. Koi technical symbols, stars (*) ya formatting mat likhna, sirf saaf bolne yogya Hindi shabda.
        """

        with st.spinner(""):
            res = run_fast_ai([genie_live_prompt])
            clean_speech = res.text.replace("*", "").replace("#", "").strip()

            # Studio-grade Neural Female Voice via High-Fi TTS Engine
            tts = gTTS(text=clean_speech, lang="hi", slow=False)
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            audio_io.seek(0)
            b64_audio = base64.b64encode(audio_io.read()).decode()

            # Autoplay Studio Audio Stream Directly
            autoplay_html = f"""
            <audio autoplay style="display:none;">
                <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
            </audio>
            """
            components.html(autoplay_html, height=0)

# ----------------- MODULE 2: FULL OCR & AUTO-FILING VAULT -----------------
elif app_mode == "📤 Parchi & Bill Auto-Filing Vault":
    st.subheader("📤 Document Upload, Visual Overlays & Auto-Filing")
    up = st.file_uploader("Parchi / Challan Dalein", type=["jpg", "jpeg", "png", "pdf"])
    if up:
        src_img = load_img(up)
        if st.button("🚀 Process Table, Math Audit & Save"):
            with st.spinner("Ledger extract aur save ho raha hai..."):
                p_ocr = """
                Extract EVERY line item from this document into JSON.
                Format:
                {
                  "category": "Mandi_Parchi" or "Truck_Logistics" or "Invoices_Bills",
                  "date": "DD/MM/YYYY or null",
                  "summary": "1 line summary",
                  "records": [
                    {
                      "party_name": "Farmer/Trader Name",
                      "weight": 25.0,
                      "rate": 2100.0,
                      "written_amount": 52500.0,
                      "doubt_flag": false,
                      "box_2d": [ymin, xmin, ymax, xmax]
                    }
                  ]
                }
                Return ONLY raw valid JSON.
                """
                try:
                    res = run_fast_ai(
                        contents=[p_ocr, build_part(src_img)],
                        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1)
                    )
                    txt = res.text.strip()
                    if txt.startswith("```json"): txt = txt[7:]
                    if txt.endswith("```"): txt = txt[:-3]
                    p_data = json.loads(txt.strip())

                    recs = p_data.get("records", [])
                    cat = p_data.get("category", "Mandi_Parchi")
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    f_path = os.path.join(STORAGE_DIR, cat, f"{ts}_{up.name}")
                    with open(f_path, "wb") as f: f.write(up.getbuffer())

                    doc_info = {
                        "doc_id": f"DOC_{ts}",
                        "filename": up.name,
                        "stored_path": f_path,
                        "category": cat,
                        "summary": p_data.get("summary"),
                        "records": recs
                    }
                    vault["documents"].append(doc_info)
                    save_vault(vault)

                    st.session_state["ocr_records"] = recs
                    st.session_state["ocr_img"] = src_img
                    st.success(f"✅ Safe ho gaya: [{cat}] folder me!")
                except Exception as e:
                    st.error(f"Error: {e}")

        if "ocr_records" in st.session_state and "ocr_img" in st.session_state:
            recs = st.session_state["ocr_records"]
            base = st.session_state["ocr_img"].copy()
            iw, ih = base.size
            df = pd.DataFrame(recs)
            draw = ImageDraw.Draw(base)

            calcs, statuses = [], []
            for _, r in df.iterrows():
                try:
                    w = float(re.sub(r"[^\d.]", "", str(r.get("weight", 0))) or 0)
                    rt = float(re.sub(r"[^\d.]", "", str(r.get("rate", 0))) or 0)
                    wa = float(re.sub(r"[^\d.]", "", str(r.get("written_amount", 0))) or 0)
                    ca = round(w * rt, 2)
                    calcs.append(ca)

                    mismatch = (wa > 0 and ca > 0 and abs(ca - wa) > 1.0)
                    doubt = bool(r.get("doubt_flag", False))
                    if mismatch:
                        statuses.append("🔴 CALC MISMATCH")
                        col = "#FF0000"
                    elif doubt:
                        statuses.append("🔴 DOUBTFUL")
                        col = "#FFA500"
                    else:
                        statuses.append("✅ 100% OK")
                        col = "#00AA00"

                    bx = r.get("box_2d")
                    if bx and len(bx) == 4:
                        y1, x1, y2, x2 = bx
                        draw.rectangle([int((x1/1000.0)*iw), int((y1/1000.0)*ih), int((x2/1000.0)*iw), int((y2/1000.0)*ih)], outline=col, width=3)
                except Exception:
                    calcs.append(0); statuses.append("🔴 ERROR")

            df["CALCULATED_AMOUNT"] = calcs
            df["STATUS"] = statuses

            c1, c2 = st.columns([1, 1])
            with c1:
                st.write("**Visual Tag Overlay:**")
                st.image(base, width="stretch")
            with c2:
                st.write("**Audited Grid:**")
                show_cols = [c for c in df.columns if c != "box_2d"]
                e_df = st.data_editor(df[show_cols], width="stretch")

                out = io.BytesIO()
                with pd.ExcelWriter(out, engine="openpyxl") as w:
                    e_df.to_excel(w, index=False, sheet_name="Mandi")
                    ws = w.sheets["Mandi"]
                    r_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                    g_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                    sc = e_df.columns.get_loc("STATUS") + 1
                    for rx in range(2, len(e_df) + 2):
                        val = str(ws.cell(row=rx, column=sc).value)
                        if "🔴" in val:
                            for cx in range(1, len(e_df.columns) + 1): ws.cell(row=rx, column=cx).fill = r_fill
                        elif "✅" in val:
                            ws.cell(row=rx, column=sc).fill = g_fill
                st.download_button("📥 Clean Audited Excel Download", data=out.getvalue(), file_name="mandi_clean.xlsx")

# ----------------- MODULE 3: DOUBT SOLVER -----------------
elif app_mode == "🧮 Hisaab Samjhein (Doubt Solver)":
    st.subheader("🔍 Instant Math Breakdown")
    f_d = st.file_uploader("Parchi Dalein", type=["jpg", "jpeg", "png", "pdf"], key="d_solv")
    query_m = st.text_input("Kya calculation samajhni hai?")
    if f_d and query_m and st.button("🧠 Explain Step-by-Step"):
        with st.spinner("Calculating..."):
            res = run_fast_ai([f"Explain mandi calculation step-by-step in Hindi for: {query_m}", build_part(load_img(f_d))])
            st.markdown(res.text)

# ----------------- MODULE 4: 2-DOCUMENT FORENSIC MATCHER -----------------
else:
    st.subheader("🔍 2-Document Forensic Cross-Check (0.0001% Variance)")
    c1, c2 = st.columns(2)
    with c1: f1 = st.file_uploader("Document 1", type=["jpg", "jpeg", "png", "pdf"], key="f1")
    with c2: f2 = st.file_uploader("Document 2", type=["jpg", "jpeg", "png", "pdf"], key="f2")
    if f1 and f2 and st.button("Run Forensic Cross-Check"):
        with st.spinner("Analyzing micro-deviations..."):
            p_comp = "Compare Doc 1 and Doc 2 strictly. Highlight any mismatch in red HTML span. Provide comparison table."
            res = run_fast_ai([p_comp, build_part(load_img(f1)), build_part(load_img(f2))])
            st.markdown(res.text, unsafe_allow_html=True)
    
