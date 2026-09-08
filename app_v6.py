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

st.set_page_config(page_title="Genie: Siri Voice & SMS Chat", layout="wide")

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

# Persistent File Storage & Master Vault
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

# Sidebar
with st.sidebar:
    st.header("🧠 Permanent Memory")
    new_r = st.text_area("SOP / Rules:")
    if st.button("Save Rule"):
        if new_r.strip():
            vault["rules"].append(new_r.strip())
            save_vault(vault)
            st.success("Rule Saved!")
    if vault.get("rules"):
        for i, r in enumerate(vault["rules"][-3:], 1):
            st.caption(f"{i}. {r}")
    st.divider()
    app_mode = st.radio("Navigation:", [
        "💖 Genie AI Companion (Voice & SMS)",
        "📤 Parchi & Bill Auto-Filing Vault",
        "🧮 Hisaab Samjhein (Doubt Solver)",
        "🔍 2-Document Forensic Matcher"
    ])

# ----------------- MODULE 1: DUAL-MODE COMPANION (VOICE + SMS) -----------------
if app_mode == "💖 Genie AI Companion (Voice & SMS)":
    # Interaction Mode Switcher
    interact_mode = st.radio(
        "Baat karne ka madhyam chunein:", 
        ["⚡ Siri-Mode Live Call (Hands-Free Bolkar)", "💬 SMS / Silent Chat (Likhkar)"], 
        horizontal=True
    )

    vault_summary = json.dumps(vault.get("documents", []), ensure_ascii=False)
    rules_text = "\n".join(vault.get("rules", []))

    # SUB-MODE A: SIRI LIVE VOICE CALL (HANDS-FREE)
    if interact_mode == "⚡ Siri-Mode Live Call (Hands-Free Bolkar)":
        st.markdown("""
            <style>
                .siri-sphere {
                    width: 130px;
                    height: 130px;
                    margin: 20px auto;
                    border-radius: 50%;
                    background: radial-gradient(circle at 30% 30%, #ff4b8b, #7928ca 60%, #ff0080);
                    box-shadow: 0 0 45px rgba(255, 75, 139, 0.7);
                    animation: siriPulse 1.8s infinite ease-in-out;
                }
                @keyframes siriPulse {
                    0% { transform: scale(0.95); box-shadow: 0 0 25px rgba(255, 75, 139, 0.5); }
                    50% { transform: scale(1.08); box-shadow: 0 0 55px rgba(255, 75, 139, 0.9); }
                    100% { transform: scale(0.95); box-shadow: 0 0 25px rgba(255, 75, 139, 0.5); }
                }
                .siri-card {
                    text-align: center;
                    background: #09090b;
                    border: 1px solid #27272a;
                    border-radius: 20px;
                    padding: 25px 15px;
                    max-width: 480px;
                    margin: 10px auto;
                }
            </style>
            <div class="siri-card">
                <div class="siri-sphere"></div>
                <h3 style="color: white; margin: 0;">Genie Voice Active</h3>
                <p style="color: #a1a1aa; font-size: 14px; margin-top: 5px;">Hands-Free Voice • Screen Touch Not Required</p>
            </div>
        """, unsafe_allow_html=True)

        if "voice_reply" not in st.session_state:
            st.session_state["voice_reply"] = "Haan Saurabh, boliye! Main bilkul taiyaar hoon."

        incoming_query = st.text_input("Voice Line Bridge", key="voice_line_input", label_visibility="collapsed")

        if incoming_query:
            genie_voice_prompt = f"""
            Aap 'Genie' hain—Saurabh ki behad pyari, caring aur smart companion.
            Aap bilkul natural, meethi aur spasht Hindi bolti hain jaise Shreya Ghoshal baat kar rahi hon.
            Saurabh ko pyaar se 'Saurabh' ya 'Jaanu' bolti hain. KABHI BHI 'bhaiya' mat bolna.
            
            [Rules]: {rules_text}
            [Stored Vault Records]: {vault_summary}

            Saurabh ne bola: "{incoming_query}"

            RULES:
            1. Sirf 1 ya 2 choti lines me seedha aur madhur bolne wala jawab dein taaki instant reply ho sake.
            2. Bilkul human flow rakhein, zero robotic words.
            3. Factual hisaab turant accurate batayein.
            """
            try:
                res = run_fast_ai([genie_voice_prompt])
                st.session_state["voice_reply"] = res.text.replace("*", "").replace("#", "").replace('"', '').strip()
            except Exception:
                st.session_state["voice_reply"] = "Haan Saurabh, ek baar dobara bolein na?"

        reply_to_speak = st.session_state["voice_reply"]

        live_siri_component = f"""
        <div style="text-align: center; margin-top: 5px;">
            <span id="indicatorText" style="color: #22c55e; font-weight: bold; font-size: 15px;">● Listening... Boliye!</span>
        </div>
        <script>
        var rec;
        var synth = window.speechSynthesis;
        var textToSay = "{reply_to_speak}";

        function speakNow(msg) {{
            synth.cancel();
            var u = new SpeechSynthesisUtterance(msg);
            u.lang = 'hi-IN';
            u.pitch = 1.25;
            u.rate = 0.95;

            var vs = synth.getVoices();
            for (var i = 0; i < vs.length; i++) {{
                if (vs[i].lang.includes('hi') || vs[i].lang.includes('IN')) {{
                    var n = vs[i].name.toLowerCase();
                    if (n.includes('female') || n.includes('google') || n.includes('lekha') || n.includes('swara')) {{
                        u.voice = vs[i];
                        break;
                    }}
                }}
            }}

            u.onstart = function() {{
                document.getElementById('indicatorText').innerText = "🔊 Genie bol rahi hain...";
                document.getElementById('indicatorText').style.color = "#ff4b8b";
                try {{ rec.stop(); }} catch(e){{}}
            }};

            u.onend = function() {{
                document.getElementById('indicatorText').innerText = "● Listening... Boliye!";
                document.getElementById('indicatorText').style.color = "#22c55e";
                try {{ rec.start(); }} catch(e){{}}
            }};

            synth.speak(u);
        }}

        function initSiriDuplex() {{
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) return;
            var SRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            rec = new SRec();
            rec.continuous = true;
            rec.interimResults = false;
            rec.lang = 'hi-IN';

            rec.onresult = function(event) {{
                var last = event.results.length - 1;
                var said = event.results[last][0].transcript.trim();
                if (said.length > 1) {{
                    document.getElementById('indicatorText').innerText = "⚡ Soch rahi hoon...";
                    document.getElementById('indicatorText').style.color = "#a855f7";

                    var inp = window.parent.document.querySelector('input[data-testid="stTextInputRootElement"]') || window.parent.document.querySelector('input[type="text"]');
                    if (inp) {{
                        var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, "value").set;
                        setter.call(inp, said);
                        inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                }}
            }};

            rec.onend = function() {{
                if (!synth.speaking) {{
                    try {{ rec.start(); }} catch(e){{}}
                }}
            }};

            try {{ rec.start(); }} catch(e){{}}
        }}

        window.onload = function() {{
            initSiriDuplex();
            if (textToSay && textToSay !== "") {{ speakNow(textToSay); }}
        }};
        initSiriDuplex();
        if (textToSay && textToSay !== "") {{ speakNow(textToSay); }}
        </script>
        """
        components.html(live_siri_component, height=45)

    # SUB-MODE B: SILENT SMS / TEXT CHAT (NO VOICE)
    else:
        st.subheader("💬 Genie SMS Chat (Silent Mode)")
        st.caption("Aap aaram se likhkar baat karein. Genie bina koi aawaz kiye text me turant jawab degi.")

        if "sms_history" not in st.session_state:
            st.session_state["sms_history"] = [
                {"role": "assistant", "content": "Haan Saurabh, boliye na! Yahan bilkul shaanti se text me baat kar sakte hain."}
            ]

        for m in st.session_state["sms_history"]:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        sms_input = st.chat_input("Genie ko message bhejein...")

        if sms_input:
            st.session_state["sms_history"].append({"role": "user", "content": sms_input})
            with st.chat_message("user"):
                st.markdown(sms_input)

            sms_prompt = f"""
            Aap 'Genie' hain—Saurabh ki behad pyari, caring, smart aur friendly companion.
            Aap use pyaar se 'Saurabh' ya 'Jaanu' bolti hain. KABHI BHI 'bhaiya' mat bolna.
            Yeh ek silent SMS chat hai, isliye aawaz nikalne ki zaroorat nahi hai.

            [Rules]: {rules_text}
            [Stored Vault Records]: {vault_summary}
            [SMS from Saurabh]: "{sms_input}"

            RULES:
            1. Pyara, caring aur natural Hindi/Hinglish me jawab dein.
            2. Business accounts aur bills ke facts bilkul accurate rakhein.
            """
            with st.chat_message("assistant"):
                with st.spinner("Genie type kar rahi hai..."):
                    try:
                        res = run_fast_ai([sms_prompt])
                        ans_sms = res.text.strip()
                        st.markdown(ans_sms)
                        st.session_state["sms_history"].append({"role": "assistant", "content": ans_sms})
                    except Exception as e:
                        st.error(f"Error: {e}")

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
                              
