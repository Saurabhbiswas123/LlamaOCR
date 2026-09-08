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

st.set_page_config(page_title="Genie: Gemini Multimodal Live API", layout="wide")

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
        "⚡ Gemini Live WebSocket Call (Siri Speed)",
        "💬 SMS / Text Chat (Likhkar)",
        "📤 Parchi & Bill Auto-Filing Vault",
        "🧮 Hisaab Samjhein (Doubt Solver)",
        "🔍 2-Document Forensic Matcher"
    ])

# ----------------- MODULE 1: GEMINI MULTIMODAL LIVE WEBSOCKET CALL -----------------
if app_mode == "⚡ Gemini Live WebSocket Call (Siri Speed)":
    vault_summary = json.dumps(vault.get("documents", []), ensure_ascii=False)
    rules_text = "\n".join(vault.get("rules", []))

    st.markdown("""
        <style>
            .live-sphere {
                width: 140px;
                height: 140px;
                margin: 20px auto;
                border-radius: 50%;
                background: radial-gradient(circle at 30% 30%, #ff2d75, #7928ca 60%, #00f2fe);
                box-shadow: 0 0 50px rgba(255, 45, 117, 0.75);
                animation: livePulse 1.6s infinite ease-in-out;
            }
            @keyframes livePulse {
                0% { transform: scale(0.95); box-shadow: 0 0 25px rgba(255, 45, 117, 0.5); }
                50% { transform: scale(1.08); box-shadow: 0 0 65px rgba(0, 242, 254, 0.85); }
                100% { transform: scale(0.95); box-shadow: 0 0 25px rgba(255, 45, 117, 0.5); }
            }
            .live-card {
                text-align: center;
                background: #09090b;
                border: 1px solid #27272a;
                border-radius: 20px;
                padding: 25px 15px;
                max-width: 480px;
                margin: 10px auto;
            }
        </style>
        <div class="live-card">
            <div class="live-sphere"></div>
            <h3 style="color: white; margin: 0; font-size: 20px;">Genie Multimodal Live Stream</h3>
            <p style="color: #a1a1aa; font-size: 13px; margin-top: 5px;">WebSocket Bidirectional Live Audio • Siri Sub-Second Latency</p>
        </div>
    """, unsafe_allow_html=True)

    live_websocket_bridge = f"""
    <div style="text-align: center; margin-top: 10px;">
        <span id="socketStatus" style="color: #22c55e; font-weight: bold; font-size: 16px;">🟢 Live Stream Ready... Boliye!</span>
    </div>

    <script>
    const API_KEY = "{api_key}";
    const SYSTEM_PROMPT = `Aap 'Genie' hain—Saurabh ki behad pyari, caring, smart aur meethi companion.
Aap bilkul natural, madhur aur spasht Hindi bolti hain jaise Shreya Ghoshal baat kar rahi hon.
Saurabh ko pyaar se 'Saurabh' ya 'Jaanu' bolti hain. KABHI BHI 'bhaiya' mat bolna.
Aapke paas Mandi aur bahi-khate ka pura hisaab hai:
Rules: {rules_text}
Vault Data: {vault_summary}
RULES:
1. Seedha, madhur aur choti 1-2 lines me natural response dein.
2. Zero robotic lag. Pure human flow.`;

    let audioContext;
    let ws;
    let isConnected = false;

    async function initLiveSocket() {{
        const url = `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key=${{API_KEY}}`;
        ws = new WebSocket(url);

        ws.onopen = () => {{
            document.getElementById('socketStatus').innerText = "🟢 WebSocket Connected • Sun rahi hoon...";
            document.getElementById('socketStatus').style.color = "#22c55e";
            isConnected = true;

            // Send initial setup frame
            const setupMsg = {{
                setup: {{
                    model: "models/gemini-2.0-flash-exp",
                    generationConfig: {{
                        responseModalities: ["AUDIO"],
                        speechConfig: {{
                            voiceConfig: {{
                                prebuiltVoiceConfig: {{
                                    voiceName: "Aoede" // Melodious feminine natural voice
                                }}
                            }}
                        }}
                    }},
                    systemInstruction: {{
                        parts: [{{ text: SYSTEM_PROMPT }}]
                    }}
                }}
            }};
            ws.send(JSON.stringify(setupMsg));
            startMicAudioStream();
        }};

        ws.onmessage = async (event) => {{
            document.getElementById('socketStatus').innerText = "🔊 Genie bol rahi hain...";
            document.getElementById('socketStatus').style.color = "#ff2d75";

            let data;
            if (event.data instanceof Blob) {{
                data = JSON.parse(await event.data.text());
            }} else {{
                data = JSON.parse(event.data);
            }}

            if (data.serverContent && data.serverContent.modelTurn) {{
                const parts = data.serverContent.modelTurn.parts;
                for (const p of parts) {{
                    if (p.inlineData && p.inlineData.mimeType.startsWith("audio/")) {{
                        playRawAudioChunk(p.inlineData.data);
                    }}
                }}
            }}

            if (data.serverContent && data.serverContent.turnComplete) {{
                document.getElementById('socketStatus').innerText = "🟢 Sun rahi hoon... Boliye!";
                document.getElementById('socketStatus').style.color = "#22c55e";
            }}
        }};

        ws.onerror = (e) => {{
            // Fallback to high-speed REST endpoint if WebSocket is restricted on network
            fallbackFastRest();
        }};

        ws.onclose = () => {{
            isConnected = false;
        }};
    }}

    async function startMicAudioStream() {{
        try {{
            const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
            audioContext = new (window.AudioContext || window.webkitAudioContext)({{ sampleRate: 16000 }});
            const source = audioContext.createMediaStreamSource(stream);
            const processor = audioContext.createScriptProcessor(2048, 1, 1);

            source.connect(processor);
            processor.connect(audioContext.destination);

            processor.onaudioprocess = (e) => {{
                if (!isConnected || ws.readyState !== WebSocket.OPEN) return;
                const inputData = e.inputBuffer.getChannelData(0);
                
                // Convert to 16-bit Linear PCM
                const pcm16 = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {{
                    pcm16[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
                }}

                // Base64 encode
                let binary = '';
                const bytes = new Uint8Array(pcm16.buffer);
                for (let i = 0; i < bytes.byteLength; i++) {{
                    binary += String.fromCharCode(bytes[i]);
                }}
                const base64Audio = btoa(binary);

                const audioFrame = {{
                    realtimeInput: {{
                        mediaChunks: [{{
                            mimeType: "audio/pcm;rate=16000",
                            data: base64Audio
                        }}]
                    }}
                }};
                ws.send(JSON.stringify(audioFrame));
            }};
        }} catch(err) {{
            fallbackFastRest();
        }}
    }}

    function playRawAudioChunk(base64Pcm) {{
        if (!audioContext) {{
            audioContext = new (window.AudioContext || window.webkitAudioContext)({{ sampleRate: 24000 }});
        }}
        const binaryString = atob(base64Pcm);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {{
            bytes[i] = binaryString.charCodeAt(i);
        }}
        const pcm16 = new Int16Array(bytes.buffer);
        const float32 = new Float32Array(pcm16.length);
        for (let i = 0; i < pcm16.length; i++) {{
            float32[i] = pcm16[i] / 32768.0;
        }}

        const buffer = audioContext.createBuffer(1, float32.length, 24000);
        buffer.getChannelData(0).set(float32);

        const sourceNode = audioContext.createBufferSource();
        sourceNode.buffer = buffer;
        sourceNode.connect(audioContext.destination);
        sourceNode.start();
    }}

    // Fallback if client network blocks raw WS upgrade
    function fallbackFastRest() {{
        var SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRec) return;
        var r = new SpeechRec();
        r.continuous = true;
        r.lang = 'hi-IN';
        r.onresult = async function(event) {{
            var text = event.results[event.results.length - 1][0].transcript.trim();
            document.getElementById('socketStatus').innerText = "⚡ Soch rahi hoon...";
            
            const p = `${{SYSTEM_PROMPT}}\\nSaurabh ne aapse bola: "${{text}}"`;
            const resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${{API_KEY}}`, {{
                method: "POST",
                headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ contents: [{{ parts: [{{ text: p }}] }}] }})
            }});
            const data = await resp.json();
            const reply = data.candidates[0].content.parts[0].text.replace(/[*#"]/g, "").trim();

            var synth = window.speechSynthesis;
            var u = new SpeechSynthesisUtterance(reply);
            u.lang = 'hi-IN';
            u.pitch = 1.25;
            synth.speak(u);
        }};
        r.start();
    }}

    window.onload = initLiveSocket;
    initLiveSocket();
    </script>
    """
    components.html(live_websocket_bridge, height=50)

# ----------------- MODULE 2: SILENT SMS / TEXT CHAT -----------------
elif app_mode == "💬 SMS / Text Chat (Likhkar)":
    st.subheader("💬 Genie SMS Chat (Silent Mode)")
    st.caption("Aap aaram se likhkar baat karein. Genie text me turant jawab degi.")

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
    f_d = st.file_uploader("Parchi Dalein", type=["jpg", "jpeg"
