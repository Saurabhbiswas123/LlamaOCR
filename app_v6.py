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

st.set_page_config(page_title="Mandi AI Master Vault & Hands-Free Assistant", layout="wide")
st.title("🌾 Mandi AI: Enterprise Autonomous Vault, Hands-Free Munim & Forensic OCR")

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
    st.subheader("🧞 Genie Voice Assistant (Always Listening)")
    st.info("💡 **Wake Word Active:** Screen ko touch kiye bina sirf boliye **'Hey Genie'** ya **'Genie'**; Genie turant active hokar aapse baat karegi.")

    handsfree_html = """
    <div style="background: #1e293b; padding: 14px; border-radius: 10px; border: 1px solid #334155; margin-bottom: 15px; display: flex; align-items: center; justify-content: space-between;">
        <div>
            <span id="genieIndicator" style="display: inline-block; width: 14px; height: 14px; border-radius: 50%; background-color: #22c55e; margin-right: 8px;"></span>
            <strong id="genieStatus" style="color: #f8fafc; font-size: 15px;">Genie sun rahi hai (Wake Word: 'Hey Genie')...</strong>
        </div>
        <button id="toggleBtn" onclick="toggleContinuousWake()" style="background: #0284c7; color: white; border: none; padding: 6px 14px; border-radius: 6px; font-weight: bold; cursor: pointer;">
            Restart Mic
        </button>
    </div>

    <script>
    var continuousRec;
    var isAwake = false;

    function initGenieListener() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            document.getElementById('genieStatus').innerText = "Browser Web Speech support nahi karta.";
            return;
        }

        var SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        continuousRec = new SpeechRec();
        continuousRec.continuous = true;
        continuousRec.interimResults = true;
        continuousRec.lang = 'hi-IN';

        continuousRec.onstart = function() {
            document.getElementById('genieIndicator').style.backgroundColor = "#22c55e";
            document.getElementById('genieStatus').innerText = "Genie sun rahi hai (Boliye 'Hey Genie')...";
        };

        continuousRec.onerror = function() {
            try { continuousRec.start(); } catch(e) {}
        };

        continuousRec.onend = function() {
            try { continuousRec.start(); } catch(e) {}
        };

        continuousRec.onresult = function(event) {
            for (var i = event.resultIndex; i < event.results.length; ++i) {
                var transcript = event.results[i][0].transcript.toLowerCase().trim();
                
                if (!isAwake && (transcript.includes("genie") || transcript.includes("gini") || transcript.includes("hey genie") || transcript.includes("he genie") || transcript.includes("ji ni"))) {
                    isAwake = true;
                    document.getElementById('genieIndicator').style.backgroundColor = "#ef4444";
                    document.getElementById('genieStatus').innerText = "🔴 Genie Active! Sawal boliye...";
                    
                    var synth = window.speechSynthesis;
                    synth.cancel();
                    var greeting = new SpeechSynthesisUtterance("Haan Saurabh ji, boliye! Kya seva karoon?");
                    greeting.lang = 'hi-IN';
                    greeting.rate = 1.0;
                    synth.speak(greeting);
                    return;
                }

                if (isAwake && event.results[i].isFinal) {
                    isAwake = false;
                    document.getElementById('genieIndicator').style.backgroundColor = "#22c55e";
                    document.getElementById('genieStatus').innerText = "Process ho raha hai: '" + transcript + "'";

                    var textInput = window.parent.document.querySelector('input[aria-label="Genie se kuch bhi poochein:"]');
                    if (textInput) {
                        textInput.value = transcript;
                        textInput.dispatchEvent(new Event('input', { bubbles: true }));
                        textInput.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }
            }
        };

        try { continuousRec.start(); } catch(e) {}
    }

    function toggleContinuousWake() {
        if (continuousRec) {
            try { continuousRec.stop(); } catch(e) {}
        }
        initGenieListener();
    }

    window.onload = initGenieListener;
    initGenieListener();
    </script>
    """
    components.html(handsfree_html, height=75)

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = [
            {"role": "assistant", "content": "Namaste Saurabh ji! Main Genie hoon, aapki apni AI Munim. Jab bhi zaroorat ho, bas boliye 'Hey Genie' aur apna sawal poochein. Main turant jawab dungi."}
        ]

    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_query = st.chat_input("Genie se kuch bhi poochein:")

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
        You are 'Genie', an authentic, warm, sharp, respectful, and friendly accounting AI partner for Saurabh Biswas's Mandi and grain trading business.
        The user addresses you as 'Genie'. You speak like a dedicated, real human partner who knows every single penny of the accounts.

        [SAVED BUSINESS RULES & SOP]:
        {persistent_rules_text}

        [ALL SAVED BUSINESS RECORDS & VAULT DOCUMENTS]:
        {json.dumps(vault_summary, ensure_ascii=False)}

        [USER QUERY]: "{user_query}"

        RULES:
        1. Always speak in natural, friendly, respectful Hindi/Hinglish.
        2. Answer directly and concisely like an expert Munim.
        3. If asked about previous bills, truck movements, farmers, weights, or amounts, fetch exact factual figures from the vault.
        4. If a document matches, mention its filename so it can be previewed.
        5. Keep responses crisp and ready for speech synthesis.
        """

        with st.chat_message("assistant"):
            with st.spinner("Genie hisaab nikaal rahi hai..."):
                try:
                    res = generate_with_fallback([genie_prompt])
                    ans_text = res.text.strip()
                    st.markdown(ans_text)
                    st.session_state["chat_history"].append({"role": "assistant", "content": ans_text})

                    matched_docs = [d for d in vault.get("documents", []) if d.get("doc_id") in ans_text or d.get("filename") in ans_text]
                    if matched_docs:
                        st.divider()
                        st.subheader("📂 Document Preview")
                        for m_doc in matched_docs:
                            p_path = m_doc.get("stored_path")
                            if p_path and os.path.exists(p_path):
                                if p_path.lower().endswith(".pdf"):
                                    pdf_rend = pdfium.PdfDocument(p_path)[0].render(scale=2).to_pil()
                                    st.image(pdf_rend, caption=m_doc.get('filename'), width=500)
                                else:
                                    st.image(Image.open(p_path), caption=m_doc.get('filename'), width=500)

                    clean_voice = ans_text.replace('"', '\\"').replace('\n', ' ')
                    components.html(f"""
                    <script>
                        var synth = window.speechSynthesis;
                        synth.cancel();
                        var utter = new SpeechSynthesisUtterance("{clean_voice}");
                        utter.lang = 'hi-IN';
                        utter.rate = 1.0;
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
            records = st.session_state["active_records"]
            base_img = st.session_state["base_image"].copy()
            img_w, img_h = base_img.size

            df = pd.DataFrame(records)
            draw = ImageDraw.Draw(base_img)

            calculated_amounts = []
            audit_status = []
            audit_remarks = []

            for idx, row in df.iterrows():
                try:
                    w = float(re.sub(r"[^\d.]", "", str(row.get("weight", 0))) or 0)
                    r = float(re.sub(r"[^\d.]", "", str(row.get("rate", 0))) or 0)
                    written_amt = float(re.sub(r"[^\d.]", "", str(row.get("written_amount", 0))) or 0)
                    correct_amt = round(w * r, 2)
                    calculated_amounts.append(correct_amt)

                    is_doubt = bool(row.get("doubt_flag", False))
                    reason = str(row.get("doubt_reason", "")).strip()

                    is_math_mismatch = (written_amt > 0 and correct_amt > 0 and abs(correct_amt - written_amt) > 1.0)
                    
                    if is_math_mismatch:
                        diff = round(written_amt - correct_amt, 2)
                        st_text = "🔴 CALC MISMATCH"
                        rm_text = f"Paper: ₹{written_amt} | Sahi: ₹{correct_amt} (Farq: ₹{diff})"
                        box_color = "#FF0000"
                    elif is_doubt:
                        st_text = "🔴 DOUBTFUL INK"
                        rm_text = reason if reason else "Ambiguous text"
                        box_color = "#FFA500"
                    else:
                        st_text = "✅ 100% OK"
                        rm_text = "Verified"
                        box_color = "#00AA00"

                    audit_status.append(st_text)
                    audit_remarks.append(rm_text)

                    box = row.get("box_2d")
                    if box and isinstance(box, list) and len(box) == 4:
                        ymin, xmin, ymax, xmax = box
                        left = int((xmin / 1000.0) * img_w)
                        top = int((ymin / 1000.0) * img_h)
                        right = int((xmax / 1000.0) * img_w)
                        bottom = int((ymax / 1000.0) * img_h)

                        draw.rectangle([left, top, right, bottom], outline=box_color, width=3)
                        tag_text = f"#{idx+1}: {'ERR' if (is_math_mismatch or is_doubt) else 'OK'}"
                        draw.rectangle([left, max(0, top-18), left+60, top], fill=box_color)
                        draw.text((left+3, max(0, top-16)), tag_text, fill="white")

                except Exception:
                    calculated_amounts.append(0)
                    audit_status.append("🔴 ERROR")
                    audit_remarks.append("Review manually")

            df["CALCULATED_AMOUNT"] = calculated_amounts
            df["AUDIT_STATUS"] = audit_status
            df["AUDIT_REMARKS"] = audit_remarks

            col_img, col_data = st.columns([1, 1])
            with col_img:
                st.subheader("🖼️ Document Visual Overlay")
                st.image(base_img, width="stretch")

            with col_data:
                st.subheader("📋 Audited Ledger Grid (Live Editable)")
                display_cols = [c for c in df.columns if c != "box_2d"]
                edited_df = st.data_editor(df[display_cols], width="stretch")

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    edited_df.to_excel(writer, index=False, sheet_name="Mandi_Verified_Data")
                    ws = writer.sheets["Mandi_Verified_Data"]

                    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                    red_font = Font(color="9C0006", bold=True)
                    green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                    green_font = Font(color="006100", bold=True)

                    status_col = edited_df.columns.get_loc("AUDIT_STATUS") + 1
                    for r_idx in range(2, len(edited_df) + 2):
                        status_val = str(ws.cell(row=r_idx, column=status_col).value)
                        if "🔴" in status_val:
                            for c_idx in range(1, len(edited_df.columns) + 1):
                                ws.cell(row=r_idx, column=c_idx).fill = red_fill
                                ws.cell(row=r_idx, column=c_idx).font = red_font
                        elif "✅" in status_val:
                            ws.cell(row=r_idx, column=status_col).fill = green_fill
                            ws.cell(row=r_idx, column=status_col).font = green_font

                st.download_button(
                    label="📥 Download Clean Audited Excel (.xlsx)",
                    data=output.getvalue(),
                    file_name="mandi_audited_clean.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            # Visual Snippet Inspector
            st.divider()
            st.subheader("🔍 Visual Crop Inspector")
            inspector_options = [f"Row {i+1} | {df.iloc[i].get('party_name', '')} | {df.iloc[i]['AUDIT_STATUS']}" for i in range(len(df))]
            selected_row_idx = st.selectbox("Inspection ke liye row chunein:", range(len(df)), format_func=lambda x: inspector_options[x])

            if selected_row_idx is not None:
                sel_row = df.iloc[selected_row_idx]
                r_box = sel_row.get("box_2d")
                if r_box and isinstance(r_box, list) and len(r_box) == 4:
                    ymin, xmin, ymax, xmax = r_box
                    c_left = max(0, int((xmin / 1000.0) * img_w) - int(img_w * 0.015))
                    c_top = max(0, int((ymin / 1000.0) * img_h) - int(img_h * 0.015))
                    c_right = min(img_w, int((xmax / 1000.0) * img_w) + int(img_w * 0.015))
                    c_bottom = min(img_h, int((ymax / 1000.0) * img_h) + int(img_h * 0.015))

                    if c_right > c_left and c_bottom > c_top:
                        cropped_img = st.session_state["base_image"].crop((c_left, c_top, c_right, c_bottom))
                        st.image(cropped_img, caption=f"Row {selected_row_idx+1} Handwriting Zoom", width=550)

            # Audio Munim Readout
            st.divider()
            st.subheader("🔊 Munim Audio Audit (Bol kar milaan karein)")
            row_options = [f"Row {i+1}: {df.iloc[i].get('party_name', '')} ({df.iloc[i]['AUDIT_STATUS']})" for i in range(len(df))]
            selected_rows = st.multiselect("Kaunsi rows sunni hain? (Khali chhodne par saari rows bolega):", range(len(df)), format_func=lambda x: row_options[x])

            rows_to_speak = selected_rows if selected_rows else list(range(len(df)))

            speech_script_lines = []
            for r_idx in rows_to_speak:
                r = df.iloc[r_idx]
                p_name = r.get('party_name', 'Vyapari')
                w = r.get('weight', 0)
                rt = r.get('rate', 0)
                calc_a = r.get('CALCULATED_AMOUNT', 0)
                status = r.get('AUDIT_STATUS', '')
                
                if "CALC MISMATCH" in status:
                    line = f"Row {r_idx+1}. {p_name}. Wazan {w}. Rate {rt}. Dhyan dein, paper par amount galat likha hai. Sahi hisaab {calc_a} banta hai."
                elif "DOUBTFUL" in status:
                    line = f"Row {r_idx+1}. {p_name}. Handwriting mein doubt hai, kripya check karein."
                else:
                    line = f"Row {r_idx+1}. {p_name}. Wazan {w}. Rate {rt}. Amount {calc_a}. Sahi match hai."
                speech_script_lines.append(line)

            full_speech_text = " ".join(speech_script_lines).replace('"', '\\"')

            tts_html = f"""
            <div style="margin-top: 8px;">
                <button onclick="speakAudit()" style="background-color: #ff4b4b; color: white; border: none; padding: 10px 18px; font-size: 15px; border-radius: 5px; cursor: pointer; font-weight: bold;">
                    🔊 Audio Sunna Shuru Karein
                </button>
                <button onclick="stopAudit()" style="background-color: #555; color: white; border: none; padding: 10px 18px; font-size: 15px; border-radius: 5px; cursor: pointer; margin-left: 10px;">
                    ⏹️ Stop
                </button>
            </div>
            <script>
                var synth = window.speechSynthesis;
                function speakAudit() {{
                    synth.cancel();
                    var text = "{full_speech_text}";
                    var utterThis = new SpeechSynthesisUtterance(text);
                    utterThis.lang = 'hi-IN';
                    utterThis.rate = 0.9;
                    synth.speak(utterThis);
                }}
                function stopAudit() {{
                    synth.cancel();
                }}
            </script>
            """
            components.html(tts_html, height=65)

# ----------------- MODULE 3: Instant Math Explanation -----------------
elif app_mode == "Explain Math (Doubt Solver)":
    st.subheader("🔍 Instant Calculation Breakdown & Explanation")
    doubt_doc = st.file_uploader("Document upload karein", type=["jpg", "jpeg", "png", "pdf"], key="d_file")
    user_math_q = st.text_input("Kis sankhya ya hisaab par doubt hai?", placeholder="e.g. Total 54,200 kaise aaya? Rate aur deduction samjhao.")

    if doubt_doc and user_math_q and st.button("🧠 Explain Step-by-Step"):
        with st.spinner("Breakdown chal raha hai..."):
            img_part = build_part_from_pil(load_source_image(doubt_doc))
            math_prompt = f"""
            You are a master Indian Mandi auditor. Break down the calculation:
            Query: "{user_math_q}"
            1. Raw weights & rates.
            2. Exact math formula applied.
            3. Did the munim make an arithmetic mistake? State the difference in Rupees.
            """
            try:
                res = generate_with_fallback([math_prompt, img_part])
                st.markdown(res.text)
            except Exception as e:
                st.error(f"Error: {e}")

# ----------------- MODULE 4: 2-Document Matcher -----------------
else:
    st.subheader("🔍 Forensic 2-Document Matcher (0.0001% Variance)")
    c1, c2 = st.columns(2)
    with c1: d1 = st.file_uploader("Document 1", type=["jpg", "jpeg", "png", "pdf"], key="d1_m")
    with c2: d2 = st.file_uploader("Document 2", type=["jpg", "jpeg", "png", "pdf"], key="d2_m")

    if d1 and d2 and st.button("Run Forensic Cross-Check"):
        with st.spinner("Analyzing micro-deviations..."):
            prompt = """
            Compare Document 1 and Document 2 down to 0.0001% variance.
            Highlight ANY mismatch using:
            `<span style='background-color: #ff4b4b; color: white; padding: 2px 5px; border-radius: 3px;'>🔴 VALUE (MISMATCH)</span>`.
            Provide:
            1. Verdict: 100% MATCH or CRITICAL DISCREPANCIES DETECTED
            2. Detailed Markdown Comparison Table
            """
            try:
                res = generate_with_fallback([prompt, build_part_from_pil(load_source_image(d1)), build_part_from_pil(load_source_image(d2))])
                st.markdown(res.text, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Audit match error: {e}")
