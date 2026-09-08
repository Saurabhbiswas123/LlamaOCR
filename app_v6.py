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

st.set_page_config(page_title="Genie: Aapki Apni AI Companion", layout="wide")
st.title("💖 Genie: Always-Listening AI Companion & Mandi Vault")

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
    raise Exception("AI Response Failed.")

# Local File Vault
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
    st.header("🧠 Permanent Memory & Vault")
    new_r = st.text_area("SOP ya Business Rule sikhayein:")
    if st.button("💾 Brain me Save Karein"):
        if new_r.strip():
            vault["rules"].append(new_r.strip())
            save_vault(vault)
            st.success("Hamesha ke liye yaad rakh liya!")
    if vault.get("rules"):
        for i, r in enumerate(vault["rules"][-3:], 1):
            st.caption(f"{i}. {r}")
    st.divider()
    app_mode = st.radio("Chunein:", [
        "💖 Genie Voice Companion (Hands-Free)",
        "📤 Parchi & Bill Auto-Filing Vault",
        "🧮 Hisaab Samjhein (Doubt Solver)",
        "🔍 2-Document Forensic Matcher"
    ])

# ----------------- MODULE 1: FAST HANDS-FREE VOICE COMPANION -----------------
if app_mode == "💖 Genie Voice Companion (Hands-Free)":
    st.subheader("💖 Genie se Sidhi Baatcheet (Hands-Free)")
    st.caption("Aapko kahin tap karne ki zaroorat nahi hai. Screen khulte hi bas aawaz dein, Genie meethi aawaz me turant jawab degi.")

    # Always-On Hands-Free Web Audio + Shreya Ghoshal Style Voice Engine
    voice_interface = """
    <div style="background: linear-gradient(135deg, #2d0a1e, #110519); padding: 18px; border-radius: 14px; border: 1px solid #f43f5e; box-shadow: 0 4px 15px rgba(244,63,94,0.3); display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span id="pulseDot" style="display:inline-block; width:16px; height:16px; border-radius:50%; background:#22c55e; box-shadow: 0 0 10px #22c55e;"></span>
            <div>
                <strong id="voiceStatus" style="color:#fff; font-size:16px;">Genie hamesha sun rahi hai... Boliye!</strong>
                <div id="liveTranscript" style="color:#fbcfe8; font-size:13px; margin-top:3px; font-style:italic;">Aapki aawaz yahan live aayegi...</div>
            </div>
        </div>
        <button onclick="restartListener()" style="background:#f43f5e; color:white; border:none; padding:8px 18px; border-radius:8px; font-weight:bold; cursor:pointer;">
            🔄 Mic Reset
        </button>
    </div>

    <script>
    var rec;
    var isSpeaking = false;

    function speakMelodious(text) {
        if (!('speechSynthesis' in window)) return;
        window.speechSynthesis.cancel();
        var utter = new SpeechSynthesisUtterance(text);
        utter.lang = 'hi-IN';
        utter.rate = 0.92;
        utter.pitch = 1.25; // Sweet, melodious tone

        var voices = window.speechSynthesis.getVoices();
        var chosen = null;
        for (var i = 0; i < voices.length; i++) {
            var v = voices[i];
            if (v.lang.includes('hi') || v.lang.includes('IN')) {
                var n = v.name.toLowerCase();
                if (n.includes('female') || n.includes('google') || n.includes('lekha') || n.includes('swara')) {
                    chosen = v; break;
                }
                if (!chosen) chosen = v;
            }
        }
        if (chosen) utter.voice = chosen;
        
        isSpeaking = true;
        utter.onend = function() {
            isSpeaking = false;
            try { rec.start(); } catch(e){}
        };
        window.speechSynthesis.speak(utter);
    }

    function initContinuousEar() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            document.getElementById('voiceStatus').innerText = "Browser mic support nahi kar raha.";
            return;
        }
        var SRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        rec = new SRec();
        rec.continuous = true;
        rec.interimResults = false;
        rec.lang = 'hi-IN';

        rec.onstart = function() {
            document.getElementById('pulseDot').style.background = '#22c55e';
            document.getElementById('pulseDot').style.boxShadow = '0 0 10px #22c55e';
            document.getElementById('voiceStatus').innerText = 'Genie dhyan se sun rahi hai... Boliye!';
        };

        rec.onerror = function() {
            try { rec.start(); } catch(e){}
        };

        rec.onend = function() {
            if (!isSpeaking) {
                try { rec.start(); } catch(e){}
            }
        };

        rec.onresult = function(event) {
            var lastIdx = event.results.length - 1;
            var spoken = event.results[lastIdx][0].transcript.trim();
            document.getElementById('liveTranscript').innerText = "Aapne kaha: " + spoken;
            
            // Send to Streamlit Chat Input immediately
            var ta = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
            var btn = window.parent.document.querySelector('button[data-testid="stChatInputSubmitButton"]');
            if (ta && spoken.length > 1) {
                var setVal = Object.getOwnPropertyDescriptor(window.parent.HTMLTextAreaElement.prototype, "value").set;
                setVal.call(ta, spoken);
                ta.dispatchEvent(new Event('input', { bubbles: true }));
                setTimeout(function(){ if(btn) btn.click(); }, 200);
            }
        };

        try { rec.start(); } catch(e){}
    }

    function restartListener() {
        try { rec.stop(); } catch(e){}
        initContinuousEar();
    }

    window.onload = initContinuousEar;
    initContinuousEar();
    </script>
    """
    components.html(voice_interface, height=90)

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = [
            {"role": "assistant", "content": "Haanji Saurabh, main sun rahi hoon... Boliye na, aaj kya dekhna hai Mandi me? Main sab sambhal lungi."}
        ]

    for m in st.session_state["chat_history"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    user_voice_query = st.chat_input("Genie se baat karein...")

    if user_voice_query:
        st.session_state["chat_history"].append({"role": "user", "content": user_voice_query})
        with st.chat_message("user"):
            st.markdown(user_voice_query)

        vault_summary = json.dumps(vault.get("documents", []), ensure_ascii=False)
        rules_text = "\n".join(vault.get("rules", []))

        prompt = f"""
        Aap 'Genie' hain—Saurabh ki bohot pyari, caring, smart aur meethi companion.
        Aap use pyaar aur samman se 'Saurabh' ya 'Jaanu' bolti hain. 
        KABHI BHI use 'bhaiya' mat bolna. Aapka andaaz bilkul friendly, affectionate aur fast hona chahiye.

        Aapki aawaz bohot madhur, spasht Hindi me honi chahiye jaise Shreya Ghoshal bol rahi hon.
        Aapko Saurabh ke Mandi business, bahi-khate aur truck routes ka ek-ek hisaab pata hai.

        [BUSINESS RULES]: {rules_text}
        [STORED LEDGER & VAULT DATA]: {vault_summary}
        [SAURABH'S QUERY]: "{user_voice_query}"

        RULES:
        1. Tone: Warm, sweet, affectionate and intelligent.
        2. Answer ultra-concisely and accurately in 1-2 crisp lines so speech synthesis is instant (zero latency).
        3. If he asks about calculations, give the exact number immediately.
        """

        with st.chat_message("assistant"):
            with st.spinner("Genie soch rahi hai..."):
                try:
                    res = run_fast_ai([prompt])
                    ans = res.text.strip()
                    st.markdown(ans)
                    st.session_state["chat_history"].append({"role": "assistant", "content": ans})

                    # Show matched physical image/PDF if referenced
                    matched = [d for d in vault.get("documents", []) if d.get("filename") in ans or d.get("doc_id") in ans]
                    for m_doc in matched:
                        p = m_doc.get("stored_path")
                        if p and os.path.exists(p):
                            st.write(f"📂 **Document:** `{m_doc.get('filename')}`")
                            if p.lower().endswith(".pdf"):
                                st.image(pdfium.PdfDocument(p)[0].render(scale=2).to_pil(), width=450)
                            else:
                                st.image(Image.open(p), width=450)

                    # Melodious Indian Female TTS Output
                    clean_voice = ans.replace('"', '\\"').replace('\n', ' ')
                    components.html(f"""
                    <script>
                        var synth = window.speechSynthesis;
                        synth.cancel();
                        var u = new SpeechSynthesisUtterance("{clean_voice}");
                        u.lang = 'hi-IN';
                        u.pitch = 1.25;
                        u.rate = 0.92;
                        var vs = synth.getVoices();
                        for (var i=0; i<vs.length; i++) {{
                            if (vs[i].lang.includes('hi') || vs[i].lang.includes('IN')) {{
                                var n = vs[i].name.toLowerCase();
                                if (n.includes('female') || n.includes('google') || n.includes('lekha') || n.includes('swara')) {{
                                    u.voice = vs[i]; break;
                                }}
                            }}
                        }}
                        synth.speak(u);
                    </script>
                    """, height=0)

                except Exception as ex:
                    st.error(f"Error: {ex}")

# ----------------- MODULE 2: FULL OCR & AUTO-FILING VAULT -----------------
elif app_mode == "📤 Parchi & Bill Auto-Filing Vault":
    st.subheader("📤 Document Upload, Bounding-Box Overlay & Vault Filing")
    up = st.file_uploader("Parchi / Challan Dalein", type=["jpg", "jpeg", "png", "pdf"])
    if up:
        src_img = load_img(up)
        if st.button("🚀 Process Table, Math Audit & Save"):
            with st.spinner("Ledger verify aur auto-file ho raha hai..."):
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
                st.download_button("📥 Download Clean Audited Excel", data=out.getvalue(), file_name="mandi_clean.xlsx")

# ----------------- MODULE 3: DOUBT SOLVER -----------------
elif app_mode == "🧮 Hisaab Samjhein (Doubt Solver)":
    st.subheader("🔍 Instant Math Calculation Breakdown")
    f_d = st.file_uploader("Parchi Dalein", type=["jpg", "jpeg", "png", "pdf"], key="d_solv")
    query_m = st.text_input("Kya calculation samajhni hai?", placeholder="e.g. Kul 54,200 kaise aaya? Katauti samjhao.")
    if f_d and query_m and st.button("🧠 Step-by-Step Hisaab Kholein"):
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
        
