import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io

st.set_page_config(page_title="Mandi OCR Tool", layout="wide")
st.title("Mandi & Ledger OCR (Excel Ready)")

api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Secrets me GEMINI_API_KEY configure karein.")
    st.stop()

genai.configure(api_key=api_key)
# Model name with -latest for robust v1beta routing
model = genai.GenerativeModel("gemini-1.5-flash-latest")

uploaded_file = st.sidebar.file_uploader("Mandi parchi ya register ki photo dalein", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image")

    if st.button("Extract Data to Table"):
        with st.spinner("Handwritten data scan ho raha hai..."):
            prompt = """
            Extract all handwritten and printed tables, ledger records, names, weights, rates, and amounts from this image.
            Convert them into a structured Markdown Table format.
            Columns should typically be: [S.No, Date, Name/Details, Weight/Qty, Rate, Total Amount].
            Only return the markdown table, no introductory or conversational text.
            """
            response = model.generate_content([prompt, image])
            st.markdown(response.text)

            try:
                lines = [line.strip() for line in response.text.strip().split("\n") if "|" in line]
                if len(lines) > 2:
                    raw_data = [[c.strip() for c in line.split("|")[1:-1]] for line in lines]
                    df = pd.DataFrame(raw_data[2:], columns=raw_data[0])
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        df.to_excel(writer, index=False)
                    st.download_button(
                        label="Download as Excel Sheet (.xlsx)",
                        data=output.getvalue(),
                        file_name="mandi_ledger_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            except Exception:
                pass
                
