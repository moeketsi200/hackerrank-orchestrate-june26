import streamlit as st
import os
import sys

# Ensure the current directory and the 'code' directory are in the path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "code"))

from PIL import Image
from code.model_client import init_client, analyze_claim_with_gemini
from code.prompting import build_user_prompt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Gemini Client
client = init_client()

st.set_page_config(page_title="Damage Claim Verifier", layout="wide")

st.title("🕵️‍♂️ Damage Claim Verifier (Demo)")
st.write("Upload an image and provide the claim details to verify visual evidence against the claim using Gemini.")

# Sidebar for inputs
with st.sidebar:
    st.header("Claim Details")
    claim_object = st.selectbox("Object Type", ["car", "laptop", "package"])
    
    user_claim = st.text_area(
        "User Claim Conversation", 
        "Customer: The screen is cracked.\nSupport: Are there any other issues?\nCustomer: No, just the screen."
    )
    
    uploaded_files = st.file_uploader("Upload Image(s)", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

# Main content area
if st.button("Process Claim", type="primary"):
    if not uploaded_files:
        st.warning("Please upload at least one image to verify the claim.")
    else:
        with st.spinner("Analyzing claim evidence..."):
            # Save uploaded files temporarily
            temp_image_paths = []
            image_ids = []
            
            os.makedirs("temp_uploads", exist_ok=True)
            for idx, file in enumerate(uploaded_files):
                img_path = f"temp_uploads/img_{idx}.jpg"
                img_id = f"img_{idx}"
                with open(img_path, "wb") as f:
                    f.write(file.getbuffer())
                temp_image_paths.append(img_path)
                image_ids.append(img_id)
            
            # Build prompt (using empty history for demo)
            prompt = build_user_prompt(
                claim_object=claim_object,
                claim_conversation=user_claim,
                evidence_requirements="Provide a clear image of the damaged part.",
                user_history_summary="No significant history.",
                user_history_flags="none",
                image_ids=image_ids
            )
            
            # Analyze
            try:
                assessment = analyze_claim_with_gemini(client, prompt, temp_image_paths)
                
                # Display Results
                st.subheader("Analysis Results")
                
                # Status banner
                status_color = "green" if assessment.claim_status == "supported" else "red" if assessment.claim_status == "contradicted" else "orange"
                st.markdown(f"### Claim Status: <span style='color:{status_color}'>{assessment.claim_status.upper()}</span>", unsafe_allow_html=True)
                
                st.write("**Justification:**", assessment.claim_status_justification)
                
                # Create columns for details
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Detected Issue:**", assessment.issue_type)
                    st.write("**Object Part:**", assessment.object_part)
                    st.write("**Severity:**", assessment.severity)
                with col2:
                    st.write("**Risk Flags:**", assessment.risk_flags)
                    st.write("**Valid Image:**", assessment.valid_image)
                    st.write("**Evidence Standard Met:**", assessment.evidence_standard_met)
                
                # Show images
                st.subheader("Submitted Evidence")
                cols = st.columns(len(uploaded_files))
                for idx, col in enumerate(cols):
                    with col:
                        st.image(uploaded_files[idx], caption=image_ids[idx], use_container_width=True)
                        
            except Exception as e:
                st.error(f"Error analyzing claim: {str(e)}")
            
            finally:
                # Cleanup temp files
                for path in temp_image_paths:
                    if os.path.exists(path):
                        os.remove(path)
