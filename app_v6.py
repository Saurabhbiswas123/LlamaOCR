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

st.set_page_config(page_title="Mandi AI - Genie Voice Munim", layout="wide")
st.title("🌾 Mandi AI: Genie (भारतीय मुनीम) & Autonomous Document Vault")

api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Secrets me GEMINI_API_KEY configure karein.")
    st.stop()

client = genai.Client(api_key=api_key)

ACTIVE_MODELS = ["gemini-3.6-flash", "gemini-3.5-flash-lite"]

def generate_with_fallback(contents, config=None):
    last_err = None
    for m in ACTIVE_MODELS:
        try:
            if config:
                return client.models.generate_content(model=m, contents=contents, config=config)
            return client.models.generate_content(model=m, contents=contents)
        except Exception as e:
            last_err = e
            continue
    raise Exception(f"AI Service Unavailable: {last_err}")

# ----------------- PHYSICAL FILE STORAGE & VAULT DIRECTORY -----------------
STORAGE_DIR = "vault_files"
INDEX_FILE = "vault_index.json"

os.makedirs(os.path.join(STORAGE_DIR, "Truck_Logistics"), exist_ok=True)
os.makedirs(os.path.join(STORAGE_DIR, "Mandi_Parchi"), exist_ok=True)
os.makedirs(os.path.join(STORAGE_DIR, "Invoices_Bills"), exist_ok=True)
os.makedirs(os.path.join(STORAGE_DIR, "General_Docs"), exist_ok=True)

def load_vault_index():
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "business_knowledge": [],
        "documents": []
    }

def save_vault_index(data):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

vault = load_vault_index()

def load_source_image(file_obj):
    if file_obj.type == "application/pdf":
        pdf = pdfium.PdfDocument(file_obj.getvalue())
        page = pdf[0]
        return page.render(scale=2).to_pil()
    else:
        return Image.open(file_obj).convert("RGB")

def build_part_from_pil(pil_img):
    enhanced = ImageEnhance.Contrast(pil_img).enhance(1.45)
    enhanced = ImageEnhance.Sharpness(enhanced).enhance(1.35)
    buf = io.BytesIO()
    enhanced.save(buf, format="JPEG", quality=95)
    return types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")

# Sidebar: Brain SOP & Navigation
with st.sidebar:
    st.header("🧠 Permanent Memory & Rules")
    new_sop = st.text_area("Business SOP / Rule sikhayein:")
    if st.button("💾 Brain me Lock Karein"):
        if new_sop.strip():
            vault["business_knowledge"].append({
                "rule": new_sop.strip(),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            save_vault_index(vault)
            st.success("Rule permanently save ho gaya!")

    if vault["business_knowledge"]:
        st.subheader("Saved Business Rules:")
        for idx, r in enumerate(vault["business_knowledge"][-3:], start=1):
            st.caption(f"{idx}. {r.get('rule')}")

    st.divider()
    app_mode = st.radio("Navigation:", [
        "Hands-Free Genie Voice Assistant",
        "Upload, OCR & Auto-Filing Vault",
        "Explain Math (Doubt Solver)",
        "2-Document Forensic Matcher"
    ])

# ----------------- MODULE 1: Hands-Free Genie Wake-Word Assistant -----------------
if app_mode == "Hands-Free Genie Voice Assistant":
    st.subheader("👩‍💼 जिनी (Genie): आपकी अपनी भारतीय डिजिटल मुनीम")
    st.caption("बोलिए **'हे जिनी' (Hey Genie)** या नीचे माइक दबाकर सीधे बात कीजिए। जिनी शुद्ध भारतीय नारी की आवाज़ में तुरंत उत्तर देगी।")

    # Fixed Web Speech Recognition + Hindi Female TTS Engine
    handsfree_html = """
    <div style="background: linear-gradient(135deg, #1e293b, #0f172a); padding: 16px; border-radius: 12px; border: 1px solid #38bdf8; margin-bottom: 15px;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span id="genieIndicator" style="display: inline-block; width: 14px; height: 14px; border-radius: 50%; background-color: #22c55e; box-shadow: 0 0 8px #22c55e;"></span>
                <strong id="genieStatus" style="color: #f8fafc; font-size: 15px;">जिनी सुन रही हैं... (बोलिए: 'हे जिनी')</strong>
            </div>
            <button onclick="startListeningManually()" style="background: #e11d48; color: white; border: none; padding: 8px 16px; border-radius: 8px; font-weight: bold; cursor: pointer;">
                🎙️ माइक दबाकर बोलें
            </button>
        </div>
        <div id="heardText" style="color: #94a3b8; font-size: 13px; margin-top: 8px; font-style: italic;">
            आप जो बोलेंगे वो यहाँ दिखेगा और सीधे जिनी तक पहुंचेगा...
        </div>
    </div>

    <script>
    var continuousRec;
    var isAwake = false;

    // Speak function with Indian Female Tone Priority
    function speakHindiFemale(text) {
        if (!('speechSynthesis' in window)) return;
        window.speechSynthesis.cancel();
        var utter = new SpeechSynthesisUtterance(text);
        utter.lang = 'hi-IN';
        utter.rate = 0.93;
        utter.pitch = 1.15; // Pleasant feminine pitch

        var voices = window.speechSynthesis.getVoices();
        var selectedVoice = null;

        // Try to pick authentic Indian female voice
        for (var i = 0; i < voices.length; i++) {
            var v = voices[i];
            if (v.lang.includes('hi') || v.lang.includes('IN')) {
                var name = v.name.toLowerCase();
                if (name.includes('female') || name.includes('lekha') || name.includes('swara') || name.includes('kalpana') || name.includes('google')) {
                    selectedVoice = v;
                    break;
                }
                if (!selectedVoice) selectedVoice = v;
            }
        }
        if (selectedVoice) utter.voice = selectedVoice;
        window.speechSynthesis.speak(utter);
    }

    function triggerStreamlitSubmission(text) {
        var parentDoc = window.parent.document;
        // Accurate Streamlit chat input selector
        var ta = parentDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');
        var btn = parentDoc.querySelector('button[data-testid="stChatInputSubmitButton"]');

        if (ta) {
            var nativeSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLTextAreaElement.prototype, "value").set;
            nativeSetter.call(ta, text);
            ta.dispatchEvent(new Event('input', { bubbles: true }));
            ta.dispatchEvent(new Event('change', { bubbles: true }));

            setTimeout(function() {
                if (btn) {
                    btn.click();
                } else {
                    ta.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Enter', 'keyCode': 13, 'which': 13, 'bubbles': true}));
                }
            }, 300);
        } else {
            console.log("Chat textarea not found");
        }
    }

    function initGenie() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            document.getElementById('genieStatus').innerText = "माइक्रोफ़ोन ब्राउज़र में सपोर्टेड नहीं है।";
            return;
        }

        var SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        continuousRec = new SpeechRec();
        continuousRec.continuous = true;
        continuousRec.interimResults = true;
        continuousRec.lang = 'hi-IN';

        continuousRec.onstart = function() {
            document.getElementById('genieIndicator').style.backgroundColor = "#22c55e";
            document.getElementById('genieStatus').innerText = "जिनी सुन रही हैं... (बोलिए: 'हे जिनी')";
        };

        continuousRec.onerror = function(e) {
            try { continuousRec.start(); } catch(err) {}
        };

        continuousRec.onend = function() {
            try { continuousRec.start(); } catch(err) {}
        };

        continuousRec.onresult = function(event) {
            for (var i = event.resultIndex; i < event.results.length; ++i) {
                var transcript = event.results[i][0].transcript.toLowerCase().trim();
                document.getElementById('heardText').innerText = "सुना: " + transcript;

                // Wake word trigger
                if (!isAwake && (transcript.includes("genie") || transcript.includes("जिनी") || transcript.includes("gini") || transcript.includes("hey genie") || transcript.includes("he genie"))) {
                    isAwake = true;
                    document.getElementById('genieIndicator').style.backgroundColor = "#e11d48";
                    document.getElementById('genieStatus').innerText = "🔴 जिनी सक्रिय हैं! अपना प्रश्न बोलिए...";
                    speakHindiFemale("नमस्ते भैया, बताइए क्या हिसाब देखना है? मैं सुन रही हूँ।");
                    return;
                }

                // If wake or final query recognized
                if (event.results[i].isFinal) {
                    var cleaned = transcript.replace(/hey genie|he genie|genie|जिनी/gi, "").trim();
                    if (cleaned.length > 2) {
                        isAwake = false;
                        document.getElementById('genieIndicator').style.backgroundColor = "#22c55e";
                        document.getElementById('genieStatus').innerText = "प्रश्न भेजा जा रहा है: '" + cleaned + "'";
                        triggerStreamlitSubmission(cleaned);
                    }
                }
            }
        };

        try { continuousRec.start(); } catch(e) {}
    }

    function startListeningManually() {
        if (continuousRec) {
            try { continuousRec.stop(); } catch(e) {}
        }
        isAwake = true;
        document.getElementById('genieIndicator').style.backgroundColor = "#e11d48";
        document.getElementById('genieStatus').innerText = "🔴 बोलिए, जिनी ध्यान से सुन रही हैं...";
        initGenie();
    }

    window.onload = initGenie;
    initGenie();
    </script>
    """
    components.html(handsfree_html, height=105)

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = [
            {"role": "assistant", "content": "नमस्ते भैया! मैं जिनी हूँ, आपकी अपनी मुनीम बहन। मंडी का कोई भी हिसाब हो, पर्ची मिलानी हो या गाड़ी का चालान देखना हो—आप बस बोलकर बताइए, मैं सब समझा दूँगी।"}
        ]

    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_query = st.chat_input("जिनी से कुछ भी पूछें...")

    if user_query:
        st.session_state["chat_history"].append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        vault_summary = []
        for doc in vault.get("documents", []):
            vault_summary.append({
                "doc_id": doc.get("doc_id"),
                "filename": doc.get("filename"),
                "category": doc.get("category"),
                "date": doc.get("date"),
                "truck_no": doc.get("truck_no"),
                "parties": doc.get("parties"),
                "summary": doc.get("summary"),
                "records": doc.get("records")
            })

        persistent_rules_text = "\n".join([r.get("rule", "") for r in vault.get("business_knowledge", [])])

        genie_prompt = f"""
        आप 'जिनी' (Genie) हैं—एक समझदार, आदरणीय, शुद्ध और मधुर हिंदी बोलने वाली भारतीय मुनीम।
        आप उपयोगकर्ता (भैया / मालिक) से एक निष्ठावान, होशियार भारतीय बहन/मुनीम की तरह बात करती हैं।

        [भाषा और लहजे के अनिवार्य नियम]:
        1. हमेशा शुद्ध, स्पष्ट, सम्मानजनक हिंदी बोलें (जैसे: "नमस्ते भैया", "जी, मैं अभी हिसाब देखकर बताती हूँ", "आप बिल्कुल चिंता मत कीजिए")।
        2. आपका लिंग STRICTLY FEMININE (स्त्रीलिंग) रहेगा:
           - "मैं देख रही हूँ", "मैं बताती हूँ", "मैंने हिसाब मिला लिया है" (कभी भी 'रहा हूँ' या 'करता हूँ' मत बोलना)।
        3. उत्तर हमेशा सीधा, स्पष्ट और सटीक रखें।
        4. जब भी मंडी के बही-खाते, गाड़ी या किसान के बारे में पूछा जाए, तो नीचे दिए गए सुरक्षित डेटा से बिल्कुल सही आंकड़े निकाल कर दें।

        [दुकान / व्यापार के नियम]:
        {persistent_rules_text}

        [पुराना सुरक्षित रिकॉर्ड और दस्तावेज़]:
        {json.dumps(vault_summary, ensure_ascii=False)}

        [यूज़र का सवाल]: "{user_query}"
        """

        with st.chat_message("assistant"):
            with st.spinner("जिनी हिसाब देख रही हैं..."):
                try:
                    res = generate_with_fallback([genie_prompt])
                    ans_text = res.text.strip()
                    st.markdown(ans_text)
                    st.session_state["chat_history"].append({"role": "assistant", "content": ans_text})

                    # Show matched documents
                    matched_docs = [d for d in vault.get("documents", []) if d.get("doc_id") in ans_text or d.get("filename") in ans_text]
                    if matched_docs:
                        st.divider()
                        st.subheader("📂 दस्तावेज़ की प्रति (Document Preview)")
                        for m_doc in matched_docs:
                            p_path = m_doc.get("stored_path")
                            if p_path and os.path.exists(p_path):
                                if p_path.lower().endswith(".pdf"):
                                    pdf_rend = pdfium.PdfDocument(p_path)[0].render(scale=2).to_pil()
                                    st.image(pdf_rend, caption=m_doc.get('filename'), width=500)
                                else:
                                    st.image(Image.open(p_path), caption=m_doc.get('filename'), width=500)

                    # Indian Female Voice Output
                    clean_voice = ans_text.replace('"', '\\"').replace('\n', ' ')
                    components.html(f"""
                    <script>
                        var synth = window.speechSynthesis;
                        synth.cancel();
                        var utter = new SpeechSynthesisUtterance("{clean_voice}");
                        utter.lang = 'hi-IN';
                        utter.rate = 0.93;
                        utter.pitch = 1.15;

                        var voices = synth.getVoices();
                        for (var i = 0; i < voices.length; i++) {{
                            var v = voices[i];
                            if (v.lang.includes('hi') || v.lang.includes('IN')) {{
                                var n = v.name.toLowerCase();
                                if (n.includes('female') || n.includes('lekha') || n.includes('swara') || n.includes('google')) {{
                                    utter.voice = v;
                                    break;
                                }}
                            }}
                        }}
                        synth.speak(utter);
                    </script>
                    """, height=0)

                except Exception as ex:
                    st.error(f"Genie error: {ex}")

# ----------------- MODULE 2: Full Ledger OCR & Auto-Filing -----------------
elif app_mode == "Upload, OCR & Auto-Filing Vault":
    st.subheader("📤 Upload Document (Auto-Filing & Forensic Math Verification)")
    up_file = st.file_uploader("Document upload karein (Parchi / Bill / Challan)", type=["jpg", "jpeg", "png", "pdf"])

    if up_file:
        source_image = load_source_image(up_file)

        if st.button("🚀 Process, Verify & Auto-Save into Vault"):
            with st.spinner("AI extraction, bounding box detection aur autonomous filing chal raha hai..."):
                prompt = """
                You are a senior forensic accountant for Indian Mandi registers.
                1. Read every line item, farmer name, weight, rate, and written amount into JSON.
                2. Extract bounding box coordinates: [ymin, xmin, ymax, xmax] (0 to 1000 scale).
                3. Classify document into exactly one category: 'Truck_Logistics', 'Mandi_Parchi', or 'Invoices_Bills'.
                4. Extract truck number, date, and overall document summary.

                JSON Output Format:
                {
                  "category": "Truck_Logistics" or "Mandi_Parchi" or "Invoices_Bills",
                  "doc_summary": "Short 1-line summary of what this document is",
                  "date": "DD/MM/YYYY or null",
                  "truck_no": "string or null",
                  "parties_involved": ["list of names"],
                  "records": [
                    {
                      "s_no": "1",
                      "party_name": "Farmer/Trader Name",
                      "item": "Makka / Crop",
                      "weight": 24.50,
                      "rate": 2200.0,
                      "written_amount": 53900.0,
                      "doubt_flag": false,
                      "doubt_reason": "",
                      "box_2d": [ymin, xmin, ymax, xmax]
                    }
                  ]
                }
                Return ONLY valid raw JSON.
                """
                try:
                    res = generate_with_fallback(
                        contents=[prompt, build_part_from_pil(source_image)],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.1
                        )
                    )

                    clean_text = res.text.strip()
                    if clean_text.startswith("```json"): clean_text = clean_text[7:]
                    if clean_text.endswith("```"): clean_text = clean_text[:-3]

                    parsed = json.loads(clean_text.strip())
                    records = parsed.get("records", [])
                    category = parsed.get("category", "Mandi_Parchi")

                    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_filename = f"{timestamp_str}_{up_file.name}"
                    save_folder = os.path.join(STORAGE_DIR, category)
                    os.makedirs(save_folder, exist_ok=True)
                    physical_path = os.path.join(save_folder, safe_filename)

                    with open(physical_path, "wb") as f:
                        f.write(up_file.getbuffer())

                    doc_entry = {
                        "doc_id": f"DOC_{timestamp_str}",
                        "filename": up_file.name,
                        "stored_path": physical_path,
                        "category": category,
                        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "date": parsed.get("date"),
                        "truck_no": parsed.get("truck_no"),
                        "summary": parsed.get("doc_summary"),
                        "parties": parsed.get("parties_involved", []),
                        "records_count": len(records),
                        "records": records
                    }

                    vault["documents"].append(doc_entry)
                    save_vault_index(vault)

                    st.session_state["active_records"] = records
                    st.session_state["base_image"] = source_image
                    st.session_state["current_doc"] = doc_entry

                    st.success(f"🎉 Document process ho kar save ho gaya: [{category}] me!")

                except Exception as ex:
                    st.error(f"Processing Error: {ex}")

        # Post-Processing
        if "active_records" in st.session_state and "base_image" in st.session_state:
            records = st.session_state["active_recor
