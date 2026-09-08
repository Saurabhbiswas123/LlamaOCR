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

st.set_page_config(page_title="Genie: Instant Siri Engine", layout="wide")

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
        "⚡ Genie Siri-Mode Live Call",
        "💬 SMS / Silent Chat",
        "📤 Parchi & Bill Auto-Filing Vault",
        "🧮 Hisaab Samjhein (Doubt Solver)",
        "🔍 2-Document Forensic Matcher"
    ])

# ----------------- MODULE 1: ZERO-LATENCY DIRECT SIRI LIVE CALL -----------------
if app_mode == "⚡ Genie Siri-Mode Live Call":
    vault_summary = json.dumps(vault.get("documents", []), ensure_ascii=False)
    rules_text = "\n".join(vault.get("rules", []))

    st.markdown("""
        <style>
            .siri-sphere {
                width: 140px;
                height: 140px;
                margin: 20px auto;
                border-radius: 50%;
                background: radial-gradient(circle at 30% 30%, #ff2d75, #7928ca 60%, #ff0080);
                box-shadow: 0 0 50px rgba(255, 45, 117, 0.75);
                animation: siriPulse 1.6s infinite ease-in-out;
            }
            @keyframes siriPulse {
                0% { transform: scale(0.95); box-shadow: 0 0 25px rgba(255, 45, 117, 0.5); }
                50% { transform: scale(1.08); box-shadow: 0 0 60px rgba(255, 45, 117, 0.95); }
                100% { transform: scale(0.95); box-shadow: 0 0 25px rgba(255, 45, 117, 0.5); }
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
            <h3 style="color: white; margin: 0; font-size: 20px;">Genie Live Voice Call</h3>
            <p style="color: #a1a1aa; font-size: 14px; margin-top: 5px;">Hands-Free Voice Active • 0.1s Fast Response</p>
        </div>
    """, unsafe_allow_html=True)

    # DIRECT BROWSER-TO-GEMINI AUDIO STREAM BRIDGE (NO RERUN DELAY)
    direct_voice_bridge = f"""
    <div style="text-align: center; margin-top: 10px;">
        <span id="bridgeStatus" style="color: #22c55e; font-weight: bold; font-size: 16px;">● Sun rahi hoon... Boliye!</span>
    </div>
    <script>
    const API_KEY = "{api_key}";
    const RULES = `{rules_text}`;
    const VAULT = `{vault_summary}`;

    var recognition;
    var synth = window.speechSynthesis;
    var isThinking = false;

    function getBestFemaleVoice() {{
        var voices = synth.getVoices();
        for (var i = 0; i < voices.length; i++) {{
            var v = voices[i];
            if (v.lang.includes('hi') || v.lang.includes('IN')) {{
                var n = v.name.toLowerCase();
                if (n.includes('google') || n.includes('female') || n.includes('lekha') || n.includes('swara')) {{
                    return v;
                }}
            }}
        }}
        return voices.find(v => v.lang.includes('hi')) || null;
    }}

    function speakReply(text) {{
        synth.cancel();
        var utter = new SpeechSynthesisUtterance(text);
        utter.lang = 'hi-IN';
        utter.pitch = 1.25;
        utter.rate = 1.0;

        var v = getBestFemaleVoice();
        if (v) utter.voice = v;

        utter.onstart = function() {{
            document.getElementById('bridgeStatus').innerText = "🔊 Genie bol rahi hain...";
            document.getElementById('bridgeStatus').style.color = "#ff2d75";
            try {{ recognition.stop(); }} catch(e){{}}
        }};

        utter.onend = function() {{
            document.getElementById('bridgeStatus').innerText = "● Sun rahi hoon... Boliye!";
            document.getElementById('bridgeStatus').style.color = "#22c55e";
            isThinking = false;
            try {{ recognition.start(); }} catch(e){{}}
        }};

        synth.speak(utter);
    }}

    async function queryGeminiDirect(userText) {{
        isThinking = true;
        document.getElementById('bridgeStatus').innerText = "⚡ Soch rahi hoon...";
        document.getElementById('bridgeStatus').style.color = "#a855f7";

        const prompt = `Aap 'Genie' hain—Saurabh ki behad pyari, madhur aur smart companion.
        Aap bilkul natural, meethi aur spasht Hindi bolti hain jaise Shreya Ghoshal baat kar rahi hon.
        Saurabh ko pyaar se 'Saurabh' ya 'Jaanu' bolti hain. KABHI BHI 'bhaiya' mat bolna.
        Rules: ${{RULES}}
        Vault Data: ${{VAULT}}
        Saurabh ne aapse bola: "${{userText}}"
        
        RULES:
        1. Sirf 1 ya 2 lines me seedha aur madhur bolne yogya jawab dein.
        2. Bilkul human-like natural conversation (zero robotic words).
        3. Factual hisaab turant accurate batayein.`;

        try {{
            const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${{API_KEY}}`, {{
                method: "POST",
                headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{
                    contents: [{{ parts: [{{ text: prompt }}] }}]
                }})
            }});
            const data = await res.json();
            const reply = data.candidates[0].content.parts[0].text.replace(/[*#"]/g, "").trim();
            speakReply(reply);
        }} catch(err) {{
            // Fallback to flash-lite
            try {{
                const res2 = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key=${{API_KEY}}`, {{
                    method: "POST",
                    headers: {{ "Content-Type": "application/json" }},
                    body: JSON.stringify({{
                        contents: [{{ parts: [{{ text: prompt }}] }}]
                    }})
                }});
                const data2 = await res2.json();
                const reply2 = data2.candidates[0].content.parts[0].text.replace(/[*#"]/g, "").trim();
                speakReply(reply2);
            }} catch(e) {{
                speakReply("Haan Saurabh, ek baar dobara bolein na?");
            }}
        }}
    }}

    function initVoiceListener() {{
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) return;
        var SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRec();
        recognition.continuous = true;
        recognition.interimResults = false;
        recognition.lang = 'hi-IN';

        recognition.onresult = function(event) {{
            if (isThinking) return;
            var last = event.results.length - 1;
            var spoken = event.results[last][0].transcript.trim();
            if (spoken.length > 1) {{
                queryGeminiDirect(spoken);
            }}
        }};

        recognition.onend = function() {{
            if (!synth.speaking && !isThinking) {{
                try {{ recognition.start(); }} catch(e){{}}
            }}
        }};

        try {{ recognition.start(); }} catch(e){{}}
    }}

    window.onload = function() {{
        initVoiceListener();
    }};
    initVoiceListener();
    </script>
    """
    components.html(direct_voice_bridge, height=50)

# ----------------- MODULE 2: SILENT SMS / TEXT CHAT -----------------
elif app_mode == "💬 SMS / Silent Chat":
    st.subheader("💬 Genie SMS Chat (Silent Mode)")
    st.caption("Likhkar baat karein. Genie bina aawaz kiye text me turant jawab degi.")

    if "sms_history" not in st.session_state:
        st.session_state["sms_history"] = [
            {"role": "assistant", "content": "Haan Saurabh, boliye na! Yahan aaram se text me baat kar sakte hain."}
        ]

    for m in st.session_state["sms_history"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    sms_input = st.chat_input("Genie ko message bhejein...")
    if sms_input:
        st.session_state["sms_history"].append({"role": "user", "content": sms_input})
        with st.chat_message("user"):
            st.markdown(sms_input)

        vault_summary = json.dumps(vault.get("documents", []), ensure_ascii=False)
        rules_text = "\n".join(vault.get("rules", []))
        sms_prompt = f"""
        Aap 'Genie' hain—Saurabh ki behad pyari, caring, smart companion.
        Aap use pyaar se 'Saurabh' ya 'Jaanu' bolti hain. KABHI BHI 'bhaiya' mat bolna.
        Yeh silent SMS chat hai.
        Rules: {rules_text}
        Vault Data: {vault_summary}
        SMS: "{sms_input}"
        """
        with st.chat_message("assistant"):
            with st.spinner("Genie type kar rahi hai..."):
                try:
                    res = run_fast_ai([sms_prompt])
                    ans = res.text.strip()
                    st.markdown(ans)
                    st.session_state["sms_history"].append({"role": "assistant", "content": ans})
                except Exception as e:
                    st.error(f"Error: {e}")

# ----------------- MODULE 3: FULL OCR & AUTO-FILING VAULT -----------------
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

# ----------------- MODULE 4: DOUBT SOLVER -----------------
elif app_mode == "🧮 Hisaab Samjhein (Doubt Solver)":
    st.subheader("🔍 Instant Math Breakdown")
    f_d = st.file_uploader("Parchi Dalein", type=["jpg", "jpeg", "png", "pdf"], key="d_solv")
    query_m = st.text_input("Kya calculation samajhni hai?")
    if f_d and query_m and st.button("🧠 Explain Step-by-Step"):
        with st.spinner("Calculating..."):
            res = run_fast_ai([f"Explain mandi calculation step-by-step in Hindi for: {query_m}", build_part(load_img(f_d))])
            st.markdown(res.text)

# ----------------- MODULE 5: 2-DOCUMENT FORENSIC MATCHER -----------------
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
