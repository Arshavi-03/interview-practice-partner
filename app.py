import streamlit as st
from interview_logic import InterviewAgent
from feedback_generator import FeedbackGenerator
from resume_parser import ResumeParser
from voice_handler import VoiceHandler
from config import (INTERVIEW_ROLES, SUPPORTED_RESUME_FORMATS, MAX_RESUME_SIZE_MB, 
                   INTERVIEW_DURATIONS, ANSWER_TIME_WARNING, ANSWER_TIME_LIMIT)
import time
from datetime import datetime, timedelta
import base64
import os

st.set_page_config(
    page_title="Interview Coach - AI Interview Practice",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set custom theme colors using Streamlit's API
st.markdown("""
<style>
    /* Let Streamlit handle text colors naturally */
    .stSelectbox label {
        color: #cbd5e1 !important;
    }
    
    /* Remove all forced color overrides on selectbox content */
    .stSelectbox [data-baseweb="select"] {
        background-color: #0f172a !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        border-radius: 0.75rem !important;
    }
    
    .stSelectbox [data-baseweb="select"]:hover {
        border-color: #10b981 !important;
    }
</style>
""", unsafe_allow_html=True)

# Load CSS from external file
def load_css():
    with open('styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# Helper function to auto-play audio
def autoplay_audio(audio_path):
    """Auto-play audio using JavaScript"""
    if audio_path and os.path.exists(audio_path):
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        audio_base64 = base64.b64encode(audio_bytes).decode()
        audio_html = f"""
            <audio autoplay>
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)

# Session state initialization
if 'interview_started' not in st.session_state:
    st.session_state.interview_started = False
if 'interview_agent' not in st.session_state:
    st.session_state.interview_agent = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'feedback_generated' not in st.session_state:
    st.session_state.feedback_generated = False
if 'selected_role' not in st.session_state:
    st.session_state.selected_role = "Software Engineer"
if 'selected_duration' not in st.session_state:
    st.session_state.selected_duration = "Standard Interview (15 min)"
if 'candidate_info' not in st.session_state:
    st.session_state.candidate_info = None
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = None
if 'voice_mode' not in st.session_state:
    st.session_state.voice_mode = True
if 'listening' not in st.session_state:
    st.session_state.listening = False
if 'input_mode' not in st.session_state:
    st.session_state.input_mode = "voice"
if 'resume_uploaded' not in st.session_state:
    st.session_state.resume_uploaded = False
if 'current_audio' not in st.session_state:
    st.session_state.current_audio = None
if 'page_title' not in st.session_state:
    st.session_state.page_title = "🎯 AI Interview Coach - Start Your Practice"
if 'audio_played' not in st.session_state:
    st.session_state.audio_played = False
if 'last_message_count' not in st.session_state:
    st.session_state.last_message_count = 0
if 'closing_message_shown' not in st.session_state:
    st.session_state.closing_message_shown = False

resume_parser = ResumeParser()
voice_handler = VoiceHandler()

# Enhanced Professional Sidebar
with st.sidebar:
    st.markdown("""
        <div class="sidebar-header">
            <div class="logo-wrapper">
                <div class="logo-icon-large">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                </div>
                <div>
                    <div class="logo-text-large">InterviewCoach</div>
                    <div class="sidebar-tagline">AI-Powered Practice Platform</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="nav-section">', unsafe_allow_html=True)
    st.markdown('<div class="nav-title">Navigation</div>', unsafe_allow_html=True)
    
    if not st.session_state.interview_started:
        st.markdown('<div class="nav-item active"><span class="nav-item-icon">🏠</span><span>Setup Interview</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="nav-item"><span class="nav-item-icon">💬</span><span>Interview Session</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="nav-item"><span class="nav-item-icon">📊</span><span>Feedback Report</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="nav-item"><span class="nav-item-icon">🏠</span><span>Setup Interview</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="nav-item active"><span class="nav-item-icon">💬</span><span>Interview Session</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="nav-item"><span class="nav-item-icon">📊</span><span>Feedback Report</span></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.interview_started and st.session_state.interview_agent:
        st.markdown('<div class="nav-section"><div class="nav-title">Session Statistics</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stats-card"><div class="stats-label">Role</div><div class="stats-value"><span class="stats-icon">👔</span>{st.session_state.selected_role}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stats-card"><div class="stats-label">Duration</div><div class="stats-value"><span class="stats-icon">⏱️</span>{st.session_state.selected_duration.split("(")[0].strip()}</div></div>', unsafe_allow_html=True)
        questions_answered = len([m for m in st.session_state.messages if m['role'] == 'user'])
        st.markdown(f'<div class="stats-card"><div class="stats-label">Questions Answered</div><div class="stats-value"><span class="stats-icon">✅</span>{questions_answered}</div></div></div>', unsafe_allow_html=True)

# Main content
if not st.session_state.interview_started:
    
    st.markdown(f'<div class="app-header"><h1 class="app-title">{st.session_state.page_title}</h1><p class="app-subtitle">AI-Powered Mock Interviews with Personalized Feedback</p></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown('<div class="config-card"><div class="card-header"><div class="card-icon">⚙️</div><div><div class="card-title">Interview Configuration</div><div class="card-subtitle">Choose your interview settings</div></div></div></div>', unsafe_allow_html=True)
        selected_role = st.selectbox("Select Role", options=list(INTERVIEW_ROLES.keys()), index=list(INTERVIEW_ROLES.keys()).index(st.session_state.selected_role), help="Choose the role you want to practice for")
        st.session_state.selected_role = selected_role
        st.markdown("<br>", unsafe_allow_html=True)
        selected_duration = st.selectbox("Interview Duration", options=list(INTERVIEW_DURATIONS.keys()), index=list(INTERVIEW_DURATIONS.keys()).index(st.session_state.selected_duration), help="Choose how long you want the interview to last")
        st.session_state.selected_duration = selected_duration
        st.markdown("<br>", unsafe_allow_html=True)
        voice_mode = st.checkbox("🎤 Enable Voice Mode", value=True, help="Practice with voice responses and get audio questions")
        st.session_state.voice_mode = voice_mode
    
    with col2:
        st.markdown('<div class="config-card"><div class="card-header"><div class="card-icon">📄</div><div><div class="card-title">Upload Resume</div><div class="card-subtitle">Required for personalized interview questions</div></div></div></div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Choose your resume file", type=["pdf", "docx", "txt"], help=f"Supported formats: PDF, DOCX, TXT (Max size: {MAX_RESUME_SIZE_MB}MB)")
        
        if uploaded_file:
            if uploaded_file.size / (1024 * 1024) <= MAX_RESUME_SIZE_MB:
                with st.spinner("🔍 Analyzing your resume..."):
                    ext = uploaded_file.name.split(".")[-1].lower()
                    resume_text, candidate_info = resume_parser.parse_resume(uploaded_file, ext)
                    
                    if candidate_info and not candidate_info.get('is_valid_resume', True):
                        st.error("❌ " + candidate_info.get('validation_message', 'This file does not appear to be a resume.'))
                        st.warning("⚠️ Please upload a valid resume/CV file containing your work experience, education, and skills.")
                        st.session_state.resume_uploaded = False
                    elif candidate_info:
                        st.session_state.candidate_info = candidate_info
                        st.session_state.resume_text = resume_text
                        st.session_state.resume_uploaded = True
                        st.success(f"✅ Resume analyzed successfully!")
                        st.markdown('<div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 0.75rem; padding: 1.25rem; margin-top: 1rem;"><div style="font-weight: 700; color: #6ee7b7; margin-bottom: 0.75rem; font-size: 1.05rem;">📋 Profile Summary</div>', unsafe_allow_html=True)
                        st.markdown(f"**Name:** {candidate_info.get('name', 'N/A')}")
                        st.markdown(f"**Experience:** {candidate_info.get('years_of_experience', 'N/A')}")
                        st.markdown(f"**Recent Role:** {candidate_info.get('recent_job_title', 'N/A')}")
                        if candidate_info.get('skills'):
                            skills = candidate_info.get('skills', [])[:5]
                            st.markdown(f"**Top Skills:** {', '.join(skills)}")
                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error(f"❌ File size exceeds {MAX_RESUME_SIZE_MB}MB limit")
        
        if not st.session_state.resume_uploaded:
            st.warning("⚠️ Please upload your resume to continue. Resume is required for personalized interview questions.")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    if st.session_state.resume_uploaded:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Interview", type="primary", use_container_width=True):
                with st.spinner("🎯 Initializing your interview..."):
                    duration_minutes = INTERVIEW_DURATIONS[st.session_state.selected_duration]
                    st.session_state.interview_agent = InterviewAgent(st.session_state.selected_role, duration_minutes=duration_minutes, candidate_info=st.session_state.candidate_info, resume_text=st.session_state.resume_text)
                    st.session_state.interview_agent.start_interview()
                    st.session_state.interview_started = True
                    st.session_state.audio_played = False
                    st.session_state.last_message_count = 0
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.interview_started:
    if st.session_state.interview_agent and st.session_state.interview_agent.is_interview_complete():
        if not st.session_state.closing_message_shown:
            remaining = st.session_state.interview_agent.get_time_remaining()
            if remaining is not None:
                mins, secs = int(remaining // 60), int(remaining % 60)
                st.markdown(f'<div class="timer-badge timer-warning">⏱️ {mins:02d}:{secs:02d}</div>', unsafe_allow_html=True)
            st.markdown('<div class="interview-page">', unsafe_allow_html=True)
            st.markdown(f'<div class="interview-header"><h2 class="interview-title">{st.session_state.selected_role} Interview</h2><p style="margin: 0.5rem 0 0 0; opacity: 0.95; position: relative; z-index: 1;">Interview Completed</p></div>', unsafe_allow_html=True)
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant" and st.session_state.voice_mode and st.session_state.current_audio:
                autoplay_audio(st.session_state.current_audio)
            st.markdown('</div>', unsafe_allow_html=True)
            st.session_state.closing_message_shown = True
            st.info("⏰ Interview completed. Generating your feedback report...")
            time.sleep(3)
            st.rerun()
        
        if not st.session_state.feedback_generated:
            st.markdown('<div class="interview-page">', unsafe_allow_html=True)
            st.title("📊 Analyzing Your Performance...")
            with st.spinner("Generating comprehensive feedback..."):
                feedback_gen = FeedbackGenerator(st.session_state.selected_role, st.session_state.interview_agent.get_conversation_history(), candidate_info=st.session_state.candidate_info)
                feedback = feedback_gen.generate_feedback()
                st.session_state.feedback = feedback
                st.session_state.feedback_generated = True
            st.markdown('</div>', unsafe_allow_html=True)
            st.rerun()
        else:
            st.markdown('<div class="interview-page">', unsafe_allow_html=True)
            st.title("🎯 Interview Feedback Report")
            st.markdown(st.session_state.feedback)
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Start New Interview", type="primary", use_container_width=True):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
            with col2:
                st.download_button("📥 Download Feedback", data=st.session_state.feedback, file_name=f"interview_feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md", mime="text/markdown", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        remaining = st.session_state.interview_agent.get_time_remaining()
        if remaining is not None:
            mins, secs = int(remaining // 60), int(remaining % 60)
            cls = "timer-badge" + (" timer-warning" if remaining <= 60 else "")
            st.markdown(f'<div class="{cls}">⏱️ {mins:02d}:{secs:02d}</div>', unsafe_allow_html=True)
        st.markdown('<div class="interview-page">', unsafe_allow_html=True)
        st.markdown(f'<div class="interview-header"><h2 class="interview-title">{st.session_state.selected_role} Interview</h2><p style="margin: 0.5rem 0 0 0; opacity: 0.95; position: relative; z-index: 1;">Answer naturally and showcase your skills professionally</p></div>', unsafe_allow_html=True)
        
        if len(st.session_state.messages) == 0:
            q = st.session_state.interview_agent.get_first_question()
            st.session_state.messages.append({"role": "assistant", "content": q})
            if st.session_state.voice_mode:
                audio_path = voice_handler.text_to_speech_realtime(q)
                if audio_path:
                    st.session_state.current_audio = audio_path
            time.sleep(0.5)
            st.rerun()
        
        current_message_count = len(st.session_state.messages)
        if current_message_count > st.session_state.last_message_count:
            last_msg = st.session_state.messages[-1]
            if last_msg["role"] == "assistant" and st.session_state.voice_mode and st.session_state.current_audio:
                autoplay_audio(st.session_state.current_audio)
                st.session_state.audio_played = True
            st.session_state.last_message_count = current_message_count
        
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎤 Voice Answer", key="voice_tab", use_container_width=True, type="primary" if st.session_state.input_mode == "voice" else "secondary"):
                st.session_state.input_mode = "voice"
                st.rerun()
        with col2:
            if st.button("⌨️ Text Answer", key="text_tab", use_container_width=True, type="primary" if st.session_state.input_mode == "text" else "secondary"):
                st.session_state.input_mode = "text"
                st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.session_state.input_mode == "voice":
            if not st.session_state.listening:
                if st.button("🎙️ Click to Speak", type="primary", use_container_width=True):
                    st.session_state.listening = True
                    st.rerun()
            else:
                st.info("🎤 Listening... Speak your answer now (will stop automatically after you finish)")
                text, error = voice_handler.listen_continuous(timeout=180)
                st.session_state.listening = False
                if text:
                    st.session_state.messages.append({"role": "user", "content": text})
                    with st.spinner("🤔 Processing your response..."):
                        next_q = st.session_state.interview_agent.get_next_question(text)
                        st.session_state.messages.append({"role": "assistant", "content": next_q})
                        if st.session_state.voice_mode:
                            audio_path = voice_handler.text_to_speech_realtime(next_q)
                            if audio_path:
                                st.session_state.current_audio = audio_path
                    
                    # CRITICAL: Check if interview ended and immediately transition
                    if st.session_state.interview_agent.is_interview_complete():
                        st.success("✅ Interview ended as requested. Generating feedback...")
                        time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ {error}")
                    time.sleep(2)
                    st.rerun()
        else:
            user_input = st.text_area("Type your answer here...", height=120, key="text_input", placeholder="Share your experience and thoughts in detail...")
            if st.button("📤 Submit Answer", type="primary", use_container_width=True):
                if user_input and user_input.strip():
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    with st.spinner("🤔 Processing your response..."):
                        next_q = st.session_state.interview_agent.get_next_question(user_input)
                        st.session_state.messages.append({"role": "assistant", "content": next_q})
                        if st.session_state.voice_mode:
                            audio_path = voice_handler.text_to_speech_realtime(next_q)
                            if audio_path:
                                st.session_state.current_audio = audio_path
                    
                    # CRITICAL: Check if interview ended and immediately transition
                    if st.session_state.interview_agent.is_interview_complete():
                        st.success("✅ Interview ended as requested. Generating feedback...")
                        time.sleep(2)
                    st.rerun()
                else:
                    st.warning("⚠️ Please enter an answer before submitting")
        st.markdown('</div></div>', unsafe_allow_html=True)