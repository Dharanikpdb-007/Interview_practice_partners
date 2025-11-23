import streamlit as st
from openai import OpenAI
import base64 # Required for image/file uploads

# ----------------------------------------------------------------------
# 1. INITIAL SETUP AND API KEY CHECK
# ----------------------------------------------------------------------

st.set_page_config(
    page_title="AI Interview Partner", 
    layout="centered"
)

# 🔑 BUG FIX: Access API key securely from Streamlit Secrets
# This ensures it works on both local and cloud deployment.
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    LLM_MODEL = "gpt-4o" # Use a multimodal model for better interviewing and file analysis
except KeyError:
    st.error("Error: OpenAI API Key (OPENAI_API_KEY) not found in Streamlit Secrets.")
    st.info("Please set the 'OPENAI_API_KEY' secret in your Streamlit Cloud settings.")
    st.stop()
  # Optional: File Upload for context (like a resume or job description)
uploaded_file = st.file_uploader(
    "Upload your Resume (PNG, JPG) or Job Description (Text/PDF) for context (Optional)", 
    type=['png', 'jpg', 'jpeg']
)

if uploaded_file and not st.session_state.uploaded_file_processed:
    
    # Check if a file was processed on previous runs to prevent re-processing
    st.session_state.uploaded_file_processed = True
    
    try:
        # Encode the file into a Base64 string for the API call
        file_bytes = uploaded_file.read()
        base64_image = base64.b64encode(file_bytes).decode('utf-8')
        
        # Define the content to be sent to the multimodal LLM
        image_content = {
            "type": "image_url",
            "image_url": {"url": f"data:{uploaded_file.type};base64,{base64_image}"}
        }
        text_content = {
            "type": "text",
            "content": (
                "The user has uploaded a file for context. Analyze this document/image. "
                "Your interview questions must now be based on the content of this file, "
                "targeting the skills and experience listed. Do not explicitly mention the "
                "image or file; just use its content to guide the interview."
            )
        }

        # Insert a new system message right after the main system prompt (index 1)
        st.session_state.messages.insert(1, {"role": "system", "content": [text_content, image_content]})
        
        st.success("File uploaded and successfully added to the AI's context!")
        st.image(uploaded_file, caption="Document added for context.", width=250)

    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.session_state.uploaded_file_processed = False # Reset flag on error
# Display all past messages in the conversation history
for message in st.session_state.messages:
    # Skip displaying the hidden 'system' messages
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            # For multimodal content (if we pass an image URL), only display the text part
            if isinstance(message["content"], str):
                st.markdown(message["content"])
            else:
                 # This handles system messages that contain the image object
                 for item in message["content"]:
                    if item["type"] == "text":
                        st.markdown(item["content"])


# ----------------------------------------------------------------------
# 4. HANDLE NEW USER INPUT AND LLM CALL
# ----------------------------------------------------------------------

if prompt := st.chat_input("Type your response here..."):
    # 1. Add the new user message to the session history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Display the user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # 3. Generate the AI response
    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""

        # 🔑 BUG FIX: Pass the ENTIRE history to the LLM for context
        stream = client.chat.completions.create(
            model=LLM_MODEL, 
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )

        # Stream the response for better UX ("typing" effect)
        for chunk in stream:
            if chunk.choices:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    response_container.markdown(full_response + "▌") # The "typing" cursor

        response_container.markdown(full_response) # Final response without cursor

    # 4. Add the final AI response to the session history for persistence
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.session_state.interview_started = True

# ----------------------------------------------------------------------
# 5. INITIAL MESSAGE ON FIRST RUN
# ----------------------------------------------------------------------

# If the app just loaded, prompt the LLM to ask the first question
if not st.session_state.interview_started and len([m for m in st.session_state.messages if m["role"] != "system"]) == 0:
    
    # Manually trigger the first assistant message using the system prompt
    with st.chat_message("assistant"):
        with st.spinner("Preparing your interview..."):
            
            # Use the current history (which contains the system prompts and potentially the image context)
            stream = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices:
                    content = chunk.choices[0].delta.content
                    if content:
                        full_response += content
                        st.markdown(full_response + "▌") 

            st.markdown(full_response) 

        # Add the first question to history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.interview_started = True
