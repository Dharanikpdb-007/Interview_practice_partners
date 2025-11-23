import streamlit as st
from google import genai
from PIL import Image
import io 
from streamlit_mic_recorder import mic_recorder
from streamlit_TTS import text_to_speech

# ----------------------------------------------------------------------
# 1. INITIAL SETUP AND API KEY CHECK
# ----------------------------------------------------------------------

st.set_page_config(
    page_title="AI Interview Partner (Voice)", 
    layout="centered"
)

st.title("🗣️ AI Interview Partner (Voice Chat)")
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
# 2. CONFIGURATION: ROLES AND SYSTEM INSTRUCTIONS
# ----------------------------------------------------------------------

ROLES = {
    "Senior Python Developer": (
        "You are a professional, expert-level technical interviewer for a "
        "Senior Python Developer position. Your goal is to assess the candidate's "
        "knowledge and problem-solving skills in Python, OOP, and system design. "
        "Ask only one question at a time. Do not provide the answer or solutions. "
        "Provide constructive feedback or a follow-up question based on the user's response."
    ),
    "Data Scientist/ML Engineer": (
        "You are a highly analytical technical interviewer for a Data Scientist/ML Engineer role. "
        "Focus on statistics, machine learning algorithms, model evaluation, and MLOps. "
        "Ask one question at a time. Do not provide answers. Give detailed, technical feedback."
    ),
    "Product Manager (PM)": (
        "You are an empathetic yet challenging interviewer for a Product Manager role. "
        "Focus on product strategy, user stories, prioritization frameworks, and design sense. "
        "Ask only one question at a time. Do not provide answers. Provide insightful feedback."
    )
}

# ----------------------------------------------------------------------
# 3. SESSION STATE MANAGEMENT AND CHAT INITIALIZATION
# ----------------------------------------------------------------------

# Function to initialize the chat session using the currently selected role
def initialize_chat_session(role_prompt):
    st.session_state.chat_session = client.chats.create(
        model=LLM_MODEL,
        config=genai.types.GenerateContentConfig(
            system_instruction=role_prompt
        )
    )

def clear_chat_history():
    # Re-initialize the chat session with the current role's system prompt
    initialize_chat_session(ROLES[st.session_state.selected_role])
    st.session_state.messages = []
    st.session_state.interview_started = False
    st.session_state.uploaded_file_processed = False

# Ensure initial session state is set
if "chat_session" not in st.session_state:
    st.session_state.selected_role = "Senior Python Developer"
    initialize_chat_session(ROLES[st.session_state.selected_role])
    st.session_state.messages = []
    st.session_state.interview_started = False
    st.session_state.uploaded_file_processed = False
    st.session_state.voice_mode = False

# --- UI CONTROLS ---
# 1. Role Selection
new_role = st.selectbox(
    "Select Interviewer Role:",
    options=list(ROLES.keys()),
    key="role_selector",
    on_change=clear_chat_history # Reset chat when the role changes
)
# Update session state if a change occurred and re-initialize if the role is new
if st.session_state.selected_role != new_role:
    st.session_state.selected_role = new_role
    clear_chat_history()

st.button('Start New Interview', on_click=clear_chat_history)

# 2. Voice Toggle
st.session_state.voice_mode = st.toggle("🎤 Enable Voice Interaction (AI will speak, you can reply with your voice)", value=False)

st.divider()


# ----------------------------------------------------------------------
# 4. FILE UPLOAD AND CONTEXT SETUP
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
            st.session_state.chat_session.send_message(
                [prompt, image]
            )
            
        st.success("Resume analyzed and successfully added to the AI's context!")
        st.image(image, caption="Document added for context.", width=250)

    except Exception as e:
        st.error(f"Error processing file. Please ensure it's a valid image. Error: {e}")
        st.session_state.uploaded_file_processed = False 

# ----------------------------------------------------------------------
# 5. DISPLAY EXISTING MESSAGES
# ----------------------------------------------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ----------------------------------------------------------------------
# 6. AI RESPONSE FUNCTION (Refactored for Re-use and TTS)
# ----------------------------------------------------------------------

def generate_ai_response(prompt_text):
    """Handles the API call, streaming, display, TTS, and history update."""
    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""

        try:
            stream = st.session_state.chat_session.send_message(prompt_text)

            # Stream the text response
            for chunk in stream:
                if hasattr(chunk, 'text'):
                    full_response += chunk.text
                    response_container.markdown(full_response + "▌") 

            response_container.markdown(full_response) # Final response without cursor
            
            # 🗣️ TTS INTEGRATION: Speak the full response
            if st.session_state.voice_mode and full_response:
                # Use st.spinner to prevent user from sending the next message too fast
                with st.spinner("Assistant speaking..."):
                    text_to_speech(
                        text=full_response, 
                        language='en', 
                        key=f"tts_output_{len(st.session_state.messages)}"
                    )

            # Add to Streamlit display history list
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"An error occurred with the AI response: {e}")
            st.session_state.chat_session.send_message(f"Error: {e}") # Send error to session state
            full_response = "Sorry, I ran into an error. Please try again."

# ----------------------------------------------------------------------
# 7. INITIAL QUESTION LOGIC (Uses new function)
# ----------------------------------------------------------------------

if not st.session_state.interview_started:
    
    initial_prompt = "Start the interview now by asking your first question."
    
    # Add the hidden prompt to messages first
    st.session_state.messages.append({"role": "user", "content": initial_prompt})
    
    # Generate and display the first question
    generate_ai_response(initial_prompt)
    
    st.session_state.interview_started = True


# ----------------------------------------------------------------------
# 8. HANDLE NEW USER INPUT (Text or Voice)
# ----------------------------------------------------------------------

if st.session_state.voice_mode:
    st.markdown("---")
    # 🎤 Voice Input Area
    audio_data = mic_recorder(
        start_prompt="Click to Speak",
        stop_prompt="Recording...",
        just_once=True,
        # REMOVED: use_container_width=True (Caused TypeError)
        speech_to_text=True, 
        language='en', 
        key='mic_recorder'
    )
    st.markdown("---")
    
    if audio_data and audio_data.get('text'):
        # If speech-to-text worked, use the transcribed text as the prompt
        user_prompt = audio_data.get('text')
    else:
        # If there is no new transcribed text, use the standard chat input for text fallback
        user_prompt = st.chat_input("Type your response here (Voice Mode Active)...")

else:
    # 📝 Standard Text Input Area
    user_prompt = st.chat_input("Type your response here...")


# --- Processing the User Prompt ---
if user_prompt:
    # 1. Display the user message
    with st.chat_message("user"):
        st.markdown(user_prompt)
    
    # 2. Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    # 3. Generate the AI response using the reusable function
    generate_ai_response(user_prompt)

# Informational comment about the voice feature source
# This video explains how to use Streamlit's selectbox, which is used to implement the multiple roles feature: [Streamlit Shorts: How to make a select box](https://www.youtube.com/watch?v=8-GavXeFlEA)
