import streamlit as st
import PIL.Image
import json
# Import the core function from the file you just created
from vision_engine import diagnose_crop_image

# --- Page Configuration ---
st.set_page_config(
    page_title="Vision Module Tester",
    page_icon="🔬",
    layout="centered"
)

st.title("🔬 AI Lead: Vision Module Tester")
st.markdown("Use this tool to verify the Gemini 1.5 Flash outputs before handing off to the backend and dashboard teams.")

# --- File Uploader ---
st.markdown("### Step 1: Upload a Test Image")
uploaded_file = st.file_uploader(
    "Choose a crop image (wheat, paddy, soybean) or an edge case:", 
    type=["jpg", "jpeg", "png"]
)

# --- Processing & Display ---
if uploaded_file is not None:
    # 1. Open the image using PIL
    image = PIL.Image.open(uploaded_file)
    
    # 2. Display the uploaded image
    st.image(image, caption="Uploaded Image", use_container_width=True)
    
    st.markdown("### Step 2: Run Diagnosis")
    # 3. Create a button to trigger the API call
    if st.button("Diagnose Image", type="primary"):
        
        # Show a loading spinner while waiting for Gemini
        with st.spinner('Analyzing image with Gemini 1.5 Flash...'):
            # Call your function from vision_engine.py
            result_dict = diagnose_crop_image(image)
        
        # 4. Display the results clearly
        st.success("Analysis Complete!")
        
        # Show the raw JSON dictionary. 
        # This is CRITICAL for Person 3 (Backend) so they know exactly what data structure to expect.
        st.markdown("**Raw JSON Output (For Backend Handoff):**")
        st.json(result_dict)
        
        # Show a formatted version of the data to prove it parses correctly
        st.markdown("**Parsed Data Preview:**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Crop Identified", value=result_dict.get("crop_identified", "N/A"))
            st.metric(label="Disease Name", value=result_dict.get("disease_name", "N/A"))
        with col2:
            st.metric(label="Confidence", value=result_dict.get("confidence", "N/A"))
            st.info(f"**Remedy:** {result_dict.get('short_remedy', 'N/A')}")