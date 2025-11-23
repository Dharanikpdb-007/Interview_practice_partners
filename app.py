import streamlit as st
from openai import OpenAI
import base64 

# ----------------------------------------------------------------------
# 1. INITIAL SETUP AND API KEY CHECK
# ----------------------------------------------------------------------

st.set_page_config(
    page_title="AI Interview Partner", 
    layout="centered"
)

st.title("🤖 AI Interview Partner")
st.caption("Practice your technical skills with a persistent AI interviewer.")

# 🔑 API Key Check (CRITICAL DEPLOYMENT STEP)
# This code securely looks for your OPENAI_API_KEY in Streamlit Secrets.
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    LLM_MODEL = "gpt-4o" # Multimodal model for image context
except KeyError:
    st.error("Error: OpenAI API Key (OPENAI_API_KEY) not found in Streamlit Secrets.")
    st.info("Please set the 'OPENAI_API_KEY' secret in your Streamlit Cloud settings.")
    st.stop()


# ----------------------------------------------------------------------
# 2. SESSION STATE MANAGEMENT (THE BUG FIX)
# ----------------------------------------------------------------------

# 🧠 CRITICAL FIX: This block MUST run before any other code tries to 
# read st.session_state to avoid the AttributeError.
if "messages" not in st.session_state:
    # Set the initial AI persona
    system_prompt = (
        "You are a professional, expert-level technical interviewer for a "
        "Senior Python Developer position. Your goal is to assess the candidate's "
        "knowledge and problem-solving skills. Ask only one question at a time. "
        "Do not provide the answer or solutions. Provide constructive feedback "
        "or a follow-up question based on the user's response."
        "Your first response must be the very first interview question."
    )
    st.session_state.messages = [
        {"role": "system", "content": system_prompt}
    ]
    st.session_state.interview_started = False
    st.session_state.uploaded_file_processed = False 
    

# Function to clear history (used by the button)
def clear_chat_history():
    # Only keep the original system prompt
    st.session_state.messages = [st.session_state.messages[0]]
    st.session_state.interview_started = False
    st.session_state.uploaded_file_processed = False
    
st.button('Start New Interview', on_click=clear_chat_history)
st.divider()


# ----------------------------------------------------------------------
# 3. FILE UPLOAD AND CONTEXT SETUP (Multimodal Support)
# ----------------------------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload your Resume (PNG, JPG) or Job Description (Text/PDF) for context (Optional)", 
    type=['png', 'jpg', 'jpeg']
)

if uploaded_file and not st.session_state.uploaded_file_processed:
    st.session_state.uploaded_file_processed = True
    
    try:
        # Read and encode the file into a Base64 string for the API call
        file_bytes = uploaded_file.read()
        base64_image = base64.b64encode(file_bytes).decode('utf-8')
        
        # Define the content for the multimodal LLM
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

        # Insert a new system message with the image context right after the main system prompt (index 1)
        st.session_state.messages.insert(1, {"role": "system", "content": [text_content, image_content]})
        
        st.success("File uploaded and successfully added to the AI's context! The interviewer will now use this information.")
        st.image(uploaded_file, caption="Document added for context.", width=250)

    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.session_state.uploaded_file_processed = False 


# ----------------------------------------------------------------------
# 4. DISPLAY EXISTING MESSAGES
# ----------------------------------------------------------------------

# Display all past messages in the conversation history
for message in st.session_state.messages:
    # Skip displaying the hidden 'system' messages
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            # Content can be a string (regular chat) or a list (multimodal system prompt)
            if isinstance(message["content"], str):
                st.markdown(message["content"])
            else:
                 # If it's the multimodal system prompt, only display the text part
                 for item in message["content"]:
                    if item["type"] == "text":
                        st.markdown(item["content"])


# ----------------------------------------------------------------------
# 5. INITIAL QUESTION LOGIC
# ----------------------------------------------------------------------

# If the app just loaded and the interview hasn't started, prompt the LLM to ask the first question
if not st.session_state.interview_started and len([m for m in st.session_state.messages if m["role"] != "system"]) == 0:
    
    with st.chat_message("assistant"):
        with st.spinner("Preparing your interview..."):
            
            # Call the LLM with the system context (including image if uploaded)
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


# ----------------------------------------------------------------------
# 6. HANDLE NEW USER INPUT AND LLM CALL
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

        # 🔑 Pass the ENTIRE history to the LLM for context
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
                    response_container.markdown(full_response + "▌") 

        response_container.markdown(full_response) # Final response without cursor

    # 4. Add the final AI response to the session history for persistence
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.session_state.interview_started = True
