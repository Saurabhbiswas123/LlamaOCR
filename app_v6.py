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

st.set_page_config(page_title="Mandi AI - World Class Enterprise OCR", layout="wide")
st.title("🌾 Mandi AI: World-Class Enterprise OCR, Forensic Audit & Genie Companion")

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
    raise Exception("AI response unavailable.")

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
    img = ImageEnhance.Contrast(pil_img).enhance(1.45)
    img = ImageEnhance.Sharpness(img).enhance(1.35)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")

with st.sidebar:
    st.header("🧠 Permanent Memory & Rules")
    new_r = st.text_area("Business SOP / Rules sikhayein:")
    if st.button("💾 Save Rule"):
        if new_r.strip():
            vault["rules"].append(new_r.strip())
            save_vault(vault)
            st.success("Rule Saved!")
    if vault.get("rules"):
        for i, r in enumerate(vault["rules"][-3:], 1):
            st.caption(f"{i}. {r}")
    st.divider()
    app_mode = st.radio("Navigation:", [
        "📤 World-Class OCR to Clean Excel (Visual Audit)",
        "⚡ Genie Siri-Mode Live Call",
        "💬 SMS / Text Chat",
        "🧮 Hisaab Samjhein (Doubt Solver)",
        "🔍 2-Document Forensic Matcher"
    ])

vault_summary = json.dumps(vault.get("documents", []), ensure_ascii=False)
rules_text = "\n".join(vault.get("rules", []))

# ----------------- MODULE 1: WORLD-CLASS OCR & CLEAN EXCEL AUDIT -----------------
if app_mode == "📤 World-Class OCR to Clean Excel (Visual Audit)":
    st.subheader("📤 Advanced Deep OCR & Forensic Ledger Audit")
    up = st.file_uploader("Kachhi Parchi, Ledger ya Tax Bill Dalein (Image / PDF)", type=["jpg", "jpeg", "png", "pdf"])

    if up:
        src_img = load_img(up)

        if st.button("🚀 Run Deep OCR Extraction & Math Audit"):
            with st.spinner("World-class vision OCR, item-by-item extraction aur coordinate mapping ho rahi hai..."):
                p_ocr = """
                You are a world-class forensic OCR engine designed for Indian Mandi registers, kachhi parchi, and grain trade bills.
                Extract EVERY SINGLE line item, farmer/trader name, weight, rate, and written amount into strict structured JSON.
                Do not miss any row, even if handwriting is complex or overlapping.

                Format:
                {
                  "category": "Mandi_Parchi" or "Truck_Logistics" or "Invoices_Bills",
                  "date": "DD/MM/YYYY or null",
                  "summary": "1 line summary",
                  "records": [
                    {
                      "s_no": 1,
                      "party_name": "Farmer or Trader Name",
                      "item": "Crop / Commodity",
                      "weight": 25.50,
                      "rate": 2100.0,
                      "written_amount": 53550.0,
                      "doubt_flag": false,
                      "doubt_reason": "",
                      "box_2d": [ymin, xmin, ymax, xmax]
                    }
                  ]
                }
                box_2d MUST be integer normalized coordinates between 0 and 1000 representing the exact bounding box of that row on the document.
                Return ONLY raw valid JSON.
                """
                try:
                    res = run_ai(
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
                    st.success(f"✅ Deep OCR extraction successful! Auto-saved into [{cat}] vault.")
                except Exception as e:
                    st.error(f"OCR Error: {e}")

        if "ocr_records" in st.session_state and "ocr_img" in st.session_state:
            recs = st.session_state["ocr_records"]
            base = st.session_state["ocr_img"].copy()
            iw, ih = base.size
            df = pd.DataFrame(recs)
            draw = ImageDraw.Draw(base)

            calcs, statuses, remarks = [], [], []
            for idx, r in df.iterrows():
                try:
                    w = float(re.sub(r"[^\d.]", "", str(r.get("weight", 0))) or 0)
                    rt = float(re.sub(r"[^\d.]", "", str(r.get("rate", 0))) or 0)
                    wa = float(re.sub(r"[^\d.]", "", str(r.get("written_amount", 0))) or 0)
                    
                    ca = round(w * rt, 2) if (w > 0 and rt > 0) else wa
                    calcs.append(ca)

                    mismatch = (wa > 0 and ca > 0 and abs(ca - wa) > 1.0)
                    doubt = bool(r.get("doubt_flag", False))
                    reason = str(r.get("doubt_reason", "")).strip()

                    if mismatch:
                        diff = round(wa - ca, 2)
                        statuses.append("🔴 CALC MISMATCH")
                        remarks.append(f"Paper: ₹{wa} | Sahi: ₹{ca} (Farq: ₹{diff})")
                        col = "#FF0000"
                    elif doubt:
                        statuses.append("🔴 DOUBTFUL")
                        remarks.append(reason if reason else "Ambiguous text")
                        col = "#FFA500"
                    else:
                        statuses.append("✅ 100% OK")
                        remarks.append("Verified")
                        col = "#00AA00"

                    bx = r.get("box_2d")
                    if bx and isinstance(bx, list) and len(bx) == 4:
                        y1, x1, y2, x2 = bx
                        left = int((x1 / 1000.0) * iw)
                        top = int((y1 / 1000.0) * ih)
                        right = int((x2 / 1000.0) * iw)
                        bottom = int((y2 / 1000.0) * ih)

                        draw.rectangle([left, top, right, bottom], outline=col, width=3)
                        tag = f"#{idx+1}"
                        draw.rectangle([left, max(0, top-16), left+35, top], fill=col)
                        draw.text((left+3, max(0, top-15)), tag, fill="white")
                except Exception:
                    calcs.append(0)
                    statuses.append("🔴 ERROR")
                    remarks.append("Manual check")

            df["CALCULATED_AMOUNT"] = calcs
            df["STATUS"] = statuses
            df["AUDIT_REMARKS"] = remarks

            c1, c2 = st.columns([1, 1])
            with c1:
                st.write("**🖼️ Document Visual Overlay (Bounding Boxes):**")
                st.image(base, width="stretch")
            with c2:
                st.write("**📋 Audited Ledger Grid (Live Editable):**")
                show_cols = [c for c in df.columns if c != "box_2d"]
                e_df = st.data_editor(df[show_cols], width="stretch")

                out = io.BytesIO()
                with pd.ExcelWriter(out, engine="openpyxl") as w:
                    e_df.to_excel(w, index=False, sheet_name="Mandi_Audited")
                    ws = w.sheets["Mandi_Audited"]
                    r_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                    r_font = Font(color="9C0006", bold=True)
                    g_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                    g_font = Font(color="006100", bold=True)
                    
                    sc = e_df.columns.get_loc("STATUS") + 1
                    for rx in range(2, len(e_df) + 2):
                        val = str(ws.cell(row=rx, column=sc).value)
                        if "🔴" in val:
                            for cx in range(1, len(e_df.columns) + 1):
                                ws.cell(row=rx, column=cx).fill = r_fill
                                ws.cell(row=rx, column=cx).font = r_font
                        elif "✅" in val:
                            ws.cell(row=rx, column=sc).fill = g_fill
                            ws.cell(row=rx, column=sc).font = g_font

                st.download_button(
                    label="📥 Download Color-Coded Clean Excel (.xlsx)",
                    data=out.getvalue(),
                    file_name="mandi_audited_clean.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            # Handwriting Zoom Inspector
            st.divider()
            st.subheader("🔍 Handwriting Zoom Inspector")
            options = [f"Row {i+1} | {df.iloc[i].get('party_name', '')} | {df.iloc[i]['STATUS']}" for i in range(len(df))]
            sel_idx = st.selectbox("Row chunein zoom dekhne ke liye:", range(len(df)), format_func=lambda x: options[x])
            if sel_idx is not None:
                sel_row = df.iloc[sel_idx]
                r_box = sel_row.get("box_2d")
                if r_box and isinstance(r_box, list) and len(r_box) == 4:
                    y1, x1, y2, x2 = r_box
                    c_left = max(0, int((x1 / 1000.0) * iw) - 10)
                    c_top = max(0, int((y1 / 1000.0) * ih) - 10)
                    c_right = min(iw, int((x2 / 1000.0) * iw) + 10)
                    c_bottom = min(ih, int((y2 / 1000.0) * ih) + 10)
                    if c_right > c_left and c_bottom > c_top:
                        crop_img = st.session_state["ocr_img"].crop((c_left, c_top, c_right, c_bottom))
                        st.image(crop_img, caption=f"Handwriting Zoom - Row #{sel_idx+1} ({sel_row.get('party_name')})", width=550)

# ----------------- MODULE 2: ZERO-LATENCY SIRI VOICE CALL -----------------
elif app_mode == "⚡ Genie Siri-Mode Live Call":
    st.markdown("""
        <style>
            .siri-sphere {
                width: 130px;
                height: 130px;
                margin: 20px auto;
                border-radius: 50%;
                background: radial-gradient(circle at 30% 30%, #ff2d75, #7928ca 60%, #00f2fe);
                box-shadow: 0 0 45px rgba(255, 45, 117, 0.75);
                animation: siriPulse 1.6s infinite ease-in-out;
            }
            @keyframes siriPulse {
                0% { transform: scale(0.95); box-shadow: 0 0 25px rgba(255, 45, 117, 0.5); }
                50% { transform: scale(1.08); box-shadow: 0 0 60px rgba(0, 242, 254, 0.85); }
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

    if "voice_answer" not in st.session_state:
        st.session_state["voice_answer"] = "Haan Saurabh, boliye! Main sun rahi hoon."

    audio_in = st.text_input("Audio Ingest Line", key="siri_voice_in", label_visibility="collapsed")
    if audio_in:
        prompt = f"""
        Aap 'Genie' hain—Saurabh ki behad pyari, madhur aur smart companion.
        Aap bilkul natural, meethi aur spasht Hindi bolti hain jaise Shreya Ghoshal baat kar rahi hon.
        Saurabh ko pyaar se 'Saurabh' ya 'Jaanu' bolti hain. KABHI BHI 'bhaiya' mat bolna.
        Rules: {rules_text}
        Vault Data: {vault_summary}
        Saurabh ne aapse bola: "{audio_in}"

        RULES:
        1. Sirf 1-2 choti lines me seedha aur madhur bolne yogya jawab dein.
        2. Bilkul natural insani boli.
        3. Factual hisaab turant accurate batayein.
        """
        try:
            res = run_ai([prompt])
            st.session_state["voice_answer"] = res.text.replace("*", "").replace("#", "").replace('"', '').strip()
        except Exception:
            st.session_state["voice_answer"] = "Haan Saurabh, main sun rahi hoon, boliye na!"

    reply_text = st.session_state["voice_answer"]

    voice_bridge_html = f"""
    <div style="text-align: center; margin-top: 5px;">
        <span id="stLabel" style="color: #22c55e; font-weight: bold; font-size: 15px;">● Sun rahi hoon... Boliye!</span>
    </div>
    <script>
    var rec;
    var synth = window.speechSynthesis;
    var textToSay = "{reply_text}";

    function getFemaleVoice() {{
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

    function speakReply(msg) {{
        synth.cancel();
        var u = new SpeechSynthesisUtterance(msg);
        u.lang = 'hi-IN';
        u.pitch = 1.25;
        u.rate = 0.95;
        var fv = getFemaleVoice();
        if (fv) u.voice = fv;

        u.onstart = function() {{
            document.getElementById('stLabel').innerText = "🔊 Genie bol rahi hain...";
            document.getElementById('stLabel').style.color = "#ff2d75";
            try {{ rec.stop(); }} catch(e){{}}
        }};

        u.onend = function() {{
            document.getElementById('stLabel').innerText = "● Sun rahi hoon... Boliye!";
            document.getElementById('stLabel').style.color = "#22c55e";
            try {{ rec.start(); }} catch(e){{}}
        }};

        synth.speak(u);
    }}

    function startListening() {{
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) return;
        var SRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        rec = new SRec();
        rec.continuous = true;
        rec.interimResults = false;
        rec.lang = 'hi-IN';

        rec.onresult = function(event) {{
            var last = event.results.length - 1;
            var spoken = event.results[last][0].transcript.trim();
            if (spoken.length > 1) {{
                document.getElementById('stLabel').innerText = "⚡ Soch rahi hoon...";
                document.getElementById('stLabel').style.color = "#a855f7";

                var inp = window.parent.document.querySelector('input[data-testid="stTextInputRootElement"]') || window.parent.document.querySelector('input[type="text"]');
                if (inp) {{
                    var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, "value").set;
                    setter.call(inp, spoken);
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
        startListening();
        if (textToSay && textToSay !== "") speakReply(textToSay);
    }};
    startListening();
    if (textToSay && textToSay !== "") speakReply(textToSay);
    </script>
    """
    components.html(voice_bridge_html, height=45)

# ----------------- MODULE 3: SILENT SMS / TEXT CHAT -----------------
elif app_mode == "💬 SMS / Text Chat":
    st.subheader("💬 Genie SMS Chat (Silent Mode)")
    st.caption("Aaram se likhkar baat karein. Genie text me turant jawab degi.")

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

        sms_prompt = f"""
        Aap 'Genie' hain—Saurabh ki behad pyari, caring, smart companion.
        Aap use pyaar se 'Saurabh' ya 'Jaanu' bolti hain. KABHI BHI 'bhaiya' mat bolna.
        Rules: {rules_text}
        Vault Data: {vault_summary}
        SMS: "{sms_input}"
        """
        with st.chat_message("assistant"):
            with st.spinner("Genie type kar rahi hai..."):
                try:
                    res = run_ai([sms_prompt])
                    ans = res.text.strip()
                    st.markdown(ans)
                    st.session_state["sms_history"].append({"role": "assistant", "content": ans})
                except Exception as e:
                    st.error(f"Error: {e}")

# ----------------- MODULE 4: DOUBT SOLVER -----------------
elif app_mode == "🧮 Hisaab Samjhein (Doubt Solver)":
    st.subheader("🔍 Instant Math Breakdow
