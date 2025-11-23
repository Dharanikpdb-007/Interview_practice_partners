import streamlit as st
from google import genai
from PIL import Image
import io 

# ----------------------------------------------------------------------
# 1. INITIAL SETUP AND API KEY CHECK
# ----------------------------------------------------------------------

st.set_page_config(
    page_title="AI Interview Partner (Gemini Free)", 
    layout="centered"
)

st.title("🤖 AI Interview Partner (Free Gemini)")
st.caption("Practice your technical skills with a persistent AI interviewer.")

# 🔑 API Key Check
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    LLM_MODEL = "gemini-2.5-flash" 
except KeyError:
    st.error("Error: GEMINI_API_KEY not found in Streamlit Secrets.")
    st.info("Please set the 'GEMINI_API_KEY' secret in your Streamlit Cloud settings.")
    st.stop()


# ----------------------------------------------------------------------
# 2. SESSION STATE MANAGEMENT AND CHAT INITIALIZATION
# ----------------------------------------------------------------------

# System instruction to define the interview persona
SYSTEM_INSTRUCTION = (
    "You are a professional, expert-level technical interviewer for a "
    "Senior Python Developer position. Your goal is to assess the candidate's "
    "knowledge and problem-solving skills. Ask only one question at a time. "
    "Do not provide the answer or solutions. Provide constructive feedback "
    "or a follow-up question based on the user's response."
)

if "chat_session" not in st.session_state:
    
    # Initialize the Gemini Chat Session with the system instruction
    st.session_state.chat_session = client.chats.create(
        model=LLM_MODEL,
        config=genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION
        )
    )
    st.session_state.messages = []
    st.session_state.interview_started = False
    st.session_state.uploaded_file_processed = False 

# Function to clear history (used by the button)
def clear_chat_history():
    st.session_state.chat_session = client.chats.create(
        model=LLM_MODEL,
        config=genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION
        )
    )
    st.session_state.messages = []
    st.session_state.interview_started = False
    st.session_state.uploaded_file_processed = False
    
st.button('Start New Interview', on_click=clear_chat_history)
st.divider()


# ----------------------------------------------------------------------
# 3. FILE UPLOAD AND CONTEXT SETUP
# ----------------------------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload your Resume (PNG, JPG) for context (Optional)", 
    type=['png', 'jpg', 'jpeg']
)

if uploaded_file and not st.session_state.uploaded_file_processed:
    st.session_state.uploaded_file_processed = True
    
    try:
        image_bytes = uploaded_file.read()
        image_stream = io.BytesIO(image_bytes)
        image = Image.open(image_stream)
        
        prompt = (
            "Analyze this resume image. The interview questions you generate "
            "must be directly based on the skills and experience listed in this resume. "
            "Do not mention the image directly, just use it for context."
        )
        
        with st.spinner("Analyzing resume..."):
            # Send the image and prompt to set context
            st.session_state.chat_session.send_message(
                [prompt, image]
            )
            
        st.success("Resume analyzed and successfully added to the AI's context! The interviewer will now use this information.")
        st.image(image, caption="Document added for context.", width=250)

    except Exception as e:
        st.error(f"Error processing file. Please ensure it's a valid image. Error: {e}")
        st.session_state.uploaded_file_processed = False 

# ----------------------------------------------------------------------
# 4. DISPLAY EXISTING MESSAGES
# ----------------------------------------------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ----------------------------------------------------------------------
# 5. INITIAL QUESTION LOGIC (FIXED)
# ----------------------------------------------------------------------

if not st.session_state.interview_started:
    
    with st.chat_message("assistant"):
        with st.spinner("Preparing your interview..."):
            
            initial_prompt = "Start the interview now by asking your first question."
            
            response = st.session_state.chat_session.send_message(
                initial_prompt
            )

            full_response = ""
            for chunk in response:
                # 🔑 FIX: Check if the 'text' attribute exists on the chunk
                if hasattr(chunk, 'text'):
                    full_response += chunk.text
                    st.markdown(full_response + "▌") 

            st.markdown(full_response) 

        st.session_state.messages.append({"role": "user", "content": initial_prompt})
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.interview_started = True


# ----------------------------------------------------------------------
# 6. HANDLE NEW USER INPUT AND LLM CALL (FIXED)
# ----------------------------------------------------------------------

if prompt := st.chat_input("Type your response here..."):
    # 1. Display the user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 2. Generate the AI response
    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""

        stream = st.session_state.chat_session.send_message(
            prompt
        )

        # Stream the response for better UX ("typing" effect)
        for chunk in stream:
            # 🔑 FIX: Check if the 'text' attribute exists on the chunk
            if hasattr(chunk, 'text'):
                full_response += chunk.text
                response_container.markdown(full_response + "▌") 

        response_container.markdown(full_response) # Final response without cursor

    # 3. Add both messages to the Streamlit display history list
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": full_response})
