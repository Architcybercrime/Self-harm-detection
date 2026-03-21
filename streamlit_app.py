import streamlit as st
import requests
import json
import time

# ── CONFIG ───────────────────────────────────────────
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Self Harm Detection System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── STYLES ───────────────────────────────────────────
st.markdown("""
<style>
.risk-high    { background:#ffebee; border-left:5px solid #c62828; padding:15px; border-radius:5px; }
.risk-low     { background:#e8f5e9; border-left:5px solid #2e7d32; padding:15px; border-radius:5px; }
.risk-medium  { background:#fff3e0; border-left:5px solid #e65100; padding:15px; border-radius:5px; }
.metric-card  { background:#e3f2fd; border-radius:10px; padding:15px; text-align:center; }
.stButton>button { width:100%; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ──────────────────────────────────────────
def get_headers():
    token = st.session_state.get('token', '')
    return {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }


def api_post(endpoint, data):
    try:
        r = requests.post(f"{API_URL}{endpoint}",
                          json=data, headers=get_headers(), timeout=30)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500


def api_get(endpoint):
    try:
        r = requests.get(f"{API_URL}{endpoint}",
                         headers=get_headers(), timeout=10)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500


def download_report(text):
    """Generate and return PDF report bytes."""
    try:
        r = requests.post(
            f"{API_URL}/api/generate-report",
            json={"text": text},
            headers=get_headers(),
            timeout=60
        )
        if r.status_code == 200:
            return r.content, True
        return None, False
    except Exception as e:
        return None, False


def show_risk(data):
    rl   = data.get('risk_level', 'UNKNOWN')
    conf = data.get('confidence', data.get('final_risk_score', 0))
    msg  = data.get('message', data.get('monitoring_message', ''))

    if rl == 'HIGH' or rl == 'CRITICAL':
        st.markdown(f"""
        <div class="risk-high">
        <h3>🚨 {rl} RISK</h3>
        <b>Confidence:</b> {conf:.1%}<br>
        <b>Message:</b> {msg}
        </div>""", unsafe_allow_html=True)
        st.error("**Support Resources:**\n- iCall: 9152987821\n- Vandrevala Foundation: 1860-2662-345\n- AASRA: 9820466627")

    elif rl == 'MEDIUM':
        st.markdown(f"""
        <div class="risk-medium">
        <h3>⚠️ MEDIUM RISK</h3>
        <b>Confidence:</b> {conf:.1%}<br>
        <b>Message:</b> {msg}
        </div>""", unsafe_allow_html=True)

    else:
        st.markdown(f"""
        <div class="risk-low">
        <h3>✅ LOW RISK</h3>
        <b>Confidence:</b> {conf:.1%}<br>
        <b>Message:</b> {msg}
        </div>""", unsafe_allow_html=True)


# ── SESSION STATE ────────────────────────────────────
if 'token' not in st.session_state:
    st.session_state.token = ''
if 'username' not in st.session_state:
    st.session_state.username = ''
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'is_guest' not in st.session_state:
    st.session_state.is_guest = False
if 'report_data' not in st.session_state:
    st.session_state.report_data = None
if 'last_text' not in st.session_state:
    st.session_state.last_text = ''


# ── LOGIN PAGE ───────────────────────────────────────
if not st.session_state.logged_in:
    st.title("🧠 Self Harm Detection System")
    st.markdown("### AI-Based Detection Using Behavioral & Physiological Indicators")
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Register", "👤 Guest Access"])

        with tab1:
            st.subheader("Login")
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login", type="primary"):
                if username and password:
                    data, code = api_post("/api/login", {
                        "username": username,
                        "password": password
                    })
                    if code == 200 and data.get('success'):
                        st.session_state.token     = data['access_token']
                        st.session_state.username  = username
                        st.session_state.logged_in = True
                        st.session_state.is_guest  = False
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(data.get('error', 'Login failed'))
                else:
                    st.warning("Please enter username and password")

        with tab2:
            st.subheader("Register")
            new_user = st.text_input("Username", key="reg_user")
            new_pass = st.text_input("Password (min 6 chars)", type="password", key="reg_pass")
            if st.button("Register", type="primary"):
                if new_user and new_pass:
                    data, code = api_post("/api/register", {
                        "username": new_user,
                        "password": new_pass
                    })
                    if code == 201:
                        st.success("Registered! Please login.")
                    else:
                        st.error(data.get('error', 'Registration failed'))
                else:
                    st.warning("Please fill all fields")

        with tab3:
            st.subheader("👤 Guest Access")
            st.info("Try the system without creating an account!")
            st.warning("⚠️ Guest limitations: No history saved, No PDF reports, No webcam/microphone")
            st.markdown("""
            **What you CAN do as guest:**
            - ✅ Text analysis
            - ✅ See risk level and indicators
            - ✅ View support resources
            - ✅ See monitoring dashboard

            **What requires login:**
            - 🔒 Download PDF reports
            - 🔒 Save prediction history
            - 🔒 Webcam & microphone analysis
            - 🔒 Video upload analysis
            - 🔒 Multimodal analysis
            """)
            if st.button("Continue as Guest →", type="primary"):
                st.session_state.logged_in = True
                st.session_state.username  = "Guest"
                st.session_state.is_guest  = True
                st.session_state.token     = ""
                st.rerun()

    st.stop()


# ── SIDEBAR ──────────────────────────────────────────
with st.sidebar:
    st.title("🧠 Self Harm Detection")

    if st.session_state.is_guest:
        st.warning("👤 Guest User")
        st.caption("Login for full access")
    else:
        st.success(f"👤 {st.session_state.username}")

    st.divider()

    if st.session_state.is_guest:
        page = st.radio("Navigation", [
            "🏠 Dashboard",
            "📝 Text Analysis",
            "📊 Monitoring",
        ])
    else:
        page = st.radio("Navigation", [
            "🏠 Dashboard",
            "📝 Text Analysis",
            "📷 Facial Analysis",
            "🎤 Speech Analysis",
            "🎬 Video Analysis",
            "🔀 Multimodal Analysis",
            "📊 Monitoring",
            "📈 History",
        ])

    st.divider()

    health, code = api_get("/api/health")
    if code == 200:
        st.success("🟢 API Online")
        st.caption(f"Accuracy: {health.get('accuracy', 'N/A')}")
        st.caption(f"Framework: {health.get('framework', 'FastAPI')}")
    else:
        st.error("🔴 API Offline")

    st.divider()
    if st.session_state.is_guest:
        if st.button("🔐 Login / Register"):
            st.session_state.logged_in = False
            st.session_state.is_guest  = False
            st.session_state.username  = ''
            st.rerun()
    else:
        if st.button("🚪 Logout"):
            st.session_state.logged_in   = False
            st.session_state.token       = ''
            st.session_state.username    = ''
            st.session_state.is_guest    = False
            st.session_state.report_data = None
            st.rerun()


# ── DASHBOARD ────────────────────────────────────────
if page == "🏠 Dashboard":
    st.title("🏠 Dashboard")
    if st.session_state.is_guest:
        st.markdown("Welcome, **Guest User**! 👋")
        st.info("🔒 Login to access full features including PDF reports and history.")
    else:
        st.markdown(f"Welcome back, **{st.session_state.username}**!")
    st.divider()

    if not st.session_state.is_guest:
        stats, _    = api_get("/api/stats")
        db_stats, _ = api_get("/api/db-stats")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Session Predictions", stats.get('total_predictions', 0))
        with col2:
            st.metric("Alerts Triggered", stats.get('alerts_triggered', 0))
        with col3:
            rate = stats.get('alert_rate', 0)
            st.metric("Alert Rate", f"{rate:.1%}")
        with col4:
            st.metric("Total DB Records", db_stats.get('total_predictions', 0))
        st.divider()

    st.subheader("⚡ Quick Analysis")
    quick_text = st.text_area("Enter text to analyze:", height=100,
                               placeholder="Type something here...")

    col1, col2 = st.columns(2)
    with col1:
        analyze_clicked = st.button("🔍 Analyze Now", type="primary", use_container_width=True)
    with col2:
        if st.session_state.is_guest:
            st.button("🔒 PDF Report (Login Required)", disabled=True, use_container_width=True)
            report_clicked = False
        else:
            report_clicked = st.button("📄 Analyze + Download Report", use_container_width=True)

    if (analyze_clicked or report_clicked) and quick_text:
        with st.spinner("Analyzing..."):
            data, code = api_post("/api/predict", {"text": quick_text})
        if code == 200:
            show_risk(data)
            if 'risk_indicators' in data:
                ri = data['risk_indicators']
                col1, col2, col3 = st.columns(3)
                col1.metric("Sentiment",        ri.get('text_sentiment', 'N/A'))
                col2.metric("Confidence Level", ri.get('confidence_level', 'N/A'))
                col3.metric("Severity",         ri.get('severity', 'N/A'))

            if report_clicked and not st.session_state.is_guest:
                with st.spinner("Generating professional PDF report..."):
                    pdf_bytes, success = download_report(quick_text)
                if success:
                    st.download_button(
                        label     = "⬇️ Download PDF Report",
                        data      = pdf_bytes,
                        file_name = "risk_assessment_report.pdf",
                        mime      = "application/pdf",
                        type      = "primary"
                    )
                    st.success("✅ Report ready! Click above to download.")
                else:
                    st.error("Failed to generate report")
        else:
            st.error(data.get('error', 'Analysis failed'))
    elif (analyze_clicked or report_clicked) and not quick_text:
        st.warning("Please enter some text")


# ── TEXT ANALYSIS ────────────────────────────────────
elif page == "📝 Text Analysis":
    st.title("📝 Text Analysis")
    st.markdown("Analyze text for self-harm risk indicators using NLP + ML (92.2% accuracy)")
    if st.session_state.is_guest:
        st.info("👤 Guest Mode — Login to download PDF reports")
    st.divider()

    text_input = st.text_area("Enter text to analyze:", height=150,
                               placeholder="Enter any text here...")

    if st.session_state.is_guest:
        col1, col2 = st.columns(2)
        with col1:
            analyze_btn = st.button("🔍 Analyze Text", type="primary", use_container_width=True)
        with col2:
            st.button("🔒 PDF Report (Login Required)", disabled=True, use_container_width=True)
        report_btn = False
        clear_btn  = False
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            analyze_btn = st.button("🔍 Analyze Text", type="primary", use_container_width=True)
        with col2:
            report_btn = st.button("📄 Generate PDF Report", use_container_width=True)
        with col3:
            clear_btn = st.button("🗑️ Clear", use_container_width=True)

    if analyze_btn and text_input:
        with st.spinner("Analyzing text..."):
            data, code = api_post("/api/predict", {"text": text_input})
            st.session_state.last_text = text_input

        if code == 200:
            st.divider()
            show_risk(data)
            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Risk Indicators")
                if 'risk_indicators' in data:
                    ri = data['risk_indicators']
                    st.metric("Text Sentiment",   ri.get('text_sentiment', 'N/A'))
                    st.metric("Confidence Level", ri.get('confidence_level', 'N/A'))
                    st.metric("Severity",         ri.get('severity', 'N/A'))

            with col2:
                st.subheader("Analysis Details")
                st.metric("Sentiment Score", f"{data.get('sentiment_score', 0):.4f}")
                st.metric("Confidence",      f"{data.get('confidence', 0):.1%}")
                st.metric("Alert",           "YES 🚨" if data.get('alert_triggered') else "NO ✅")

            if data.get('alert_triggered') and 'recommendations' in data:
                st.divider()
                st.subheader("📞 Support Resources")
                for resource in data['recommendations'].get('support_resources', []):
                    st.info(f"📱 {resource}")

            if not st.session_state.is_guest:
                st.divider()
                st.info("💡 Click **Generate PDF Report** to download a professional clinical report!")
        else:
            st.error(f"Error: {data.get('error', 'Unknown error')}")

    if not st.session_state.is_guest and report_btn and text_input:
        with st.spinner("Generating professional psychological report..."):
            pdf_bytes, success = download_report(text_input)
        if success:
            st.success("✅ Professional report generated!")
            st.download_button(
                label     = "⬇️ Download Professional PDF Report",
                data      = pdf_bytes,
                file_name = f"risk_assessment_{st.session_state.username}.pdf",
                mime      = "application/pdf",
                type      = "primary"
            )
        else:
            st.error("Failed to generate report. Make sure API is running.")
    elif not st.session_state.is_guest and report_btn and not text_input:
        st.warning("Please enter text first before generating report!")


# ── FACIAL ANALYSIS ──────────────────────────────────
elif page == "📷 Facial Analysis":
    st.title("📷 Facial Analysis")
    st.markdown("Real-time emotion detection using DeepFace + webcam")
    st.divider()

    st.info("📸 Click the button below to capture your webcam and analyze facial emotions")

    if st.button("📷 Capture Webcam & Analyze", type="primary"):
        with st.spinner("Capturing webcam and analyzing emotions..."):
            data, code = api_post("/api/analyze-face", {"use_webcam": True})

        if code == 200 and data.get('success'):
            st.success(f"Dominant Emotion: **{data.get('dominant_emotion', 'N/A').upper()}**")

            emotions = data.get('emotions', {})
            if emotions:
                st.subheader("Emotion Scores")
                for emotion, score in sorted(emotions.items(),
                                             key=lambda x: x[1], reverse=True):
                    st.progress(score/100, text=f"{emotion.capitalize()}: {score:.1f}%")

            st.divider()
            col1, col2 = st.columns(2)
            col1.metric("Facial Risk Score", f"{data.get('facial_risk_score', 0):.4f}")
            col2.metric("Risk Level",        data.get('risk_level', 'N/A'))
        else:
            st.error(f"Error: {data.get('error', 'Webcam failed')}")

    st.divider()
    st.subheader("Or Upload an Image")
    uploaded = st.file_uploader("Upload face image", type=['jpg', 'jpeg', 'png'])
    if uploaded and st.button("Analyze Image"):
        import base64
        b64 = base64.b64encode(uploaded.read()).decode()
        with st.spinner("Analyzing image..."):
            data, code = api_post("/api/analyze-face", {"image_base64": b64})
        if code == 200:
            st.success(f"Dominant Emotion: **{data.get('dominant_emotion', 'N/A')}**")
            emotions = data.get('emotions', {})
            for emotion, score in sorted(emotions.items(),
                                         key=lambda x: x[1], reverse=True):
                st.progress(score/100, text=f"{emotion}: {score:.1f}%")
        else:
            st.error(data.get('error', 'Analysis failed'))


# ── SPEECH ANALYSIS ──────────────────────────────────
elif page == "🎤 Speech Analysis":
    st.title("🎤 Speech Analysis")
    st.markdown("Analyze speech tone, pitch, and energy using Librosa")
    st.divider()

    st.info("🎙️ Click record and speak for the selected duration")
    duration = st.slider("Recording duration (seconds)", 3, 15, 5)

    if st.button("🎤 Record & Analyze", type="primary"):
        with st.spinner(f"Recording for {duration} seconds... SPEAK NOW!"):
            data, code = api_post("/api/analyze-speech", {
                "use_microphone": True,
                "duration":       duration
            })

        if code == 200 and data.get('success'):
            st.success("Analysis complete!")

            col1, col2, col3 = st.columns(3)
            col1.metric("Tempo (BPM)",   f"{data.get('tempo_bpm', 0):.1f}")
            col2.metric("Pitch (Hz)",    f"{data.get('avg_pitch_hz', 0):.1f}")
            col3.metric("Energy Level",  f"{data.get('energy_level', 0):.4f}")

            st.divider()
            col1, col2 = st.columns(2)
            col1.metric("Speech Risk Score", f"{data.get('speech_risk_score', 0):.4f}")
            col2.metric("Risk Level",        data.get('risk_level', 'N/A'))

            if data.get('transcription'):
                st.subheader("📝 Transcription")
                st.info(data['transcription'])

            if data.get('interpretation'):
                st.subheader("🔍 Interpretation")
                st.write(data['interpretation'])
        else:
            st.error(f"Error: {data.get('error', 'Recording failed')}")


# ── VIDEO ANALYSIS ───────────────────────────────────
elif page == "🎬 Video Analysis":
    st.title("🎬 Video Analysis")
    st.markdown("Upload a video to analyze facial expressions frame by frame")
    st.divider()

    st.info("""
    📹 **How it works:**
    - Upload any video (MP4, AVI, MOV, MKV, WEBM)
    - System samples frames every 2 seconds
    - Analyzes facial emotions in each frame
    - Generates overall risk assessment
    - Provides frame-by-frame timeline
    """)

    uploaded_video = st.file_uploader(
        "Upload Video File",
        type=['mp4', 'avi', 'mov', 'mkv', 'webm'],
        help="Max recommended size: 50MB"
    )

    if uploaded_video:
        st.video(uploaded_video)
        st.info(f"📁 File: **{uploaded_video.name}** | Size: **{uploaded_video.size/1024/1024:.1f} MB**")

        if st.button("🎬 Analyze Video", type="primary"):
            with st.spinner("Uploading and analyzing video... This may take a few minutes..."):
                try:
                    token = st.session_state.get('token', '')
                    response = requests.post(
                        f"{API_URL}/api/analyze-video",
                        files={"file": (uploaded_video.name, uploaded_video.getvalue(),
                                       uploaded_video.type)},
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=300
                    )
                    data = response.json()
                    code = response.status_code
                except Exception as e:
                    data = {"error": str(e)}
                    code = 500

            if code == 200 and data.get('success'):
                st.divider()

                # Overall risk
                overall_risk = data.get('overall_risk_level', 'UNKNOWN')
                alert        = data.get('alert_triggered', False)

                if overall_risk == 'HIGH':
                    st.error(f"🚨 **Overall Risk Level: {overall_risk}**")
                    st.error("**Support Resources:**\n- iCall: 9152987821\n- Vandrevala Foundation: 1860-2662-345\n- AASRA: 9820466627")
                elif overall_risk == 'MEDIUM':
                    st.warning(f"⚠️ **Overall Risk Level: {overall_risk}**")
                else:
                    st.success(f"✅ **Overall Risk Level: {overall_risk}**")

                st.info(data.get('message', ''))
                st.divider()

                # Video metadata
                meta = data.get('video_metadata', {})
                st.subheader("📊 Video Information")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Duration",        f"{meta.get('duration_seconds', 0):.1f}s")
                col2.metric("FPS",             f"{meta.get('fps', 0):.1f}")
                col3.metric("Resolution",      meta.get('resolution', 'N/A'))
                col4.metric("Frames Analyzed", meta.get('analyzed_frames', 0))

                # Facial analysis results
                facial = data.get('facial_analysis')
                if facial:
                    st.divider()
                    st.subheader("😊 Facial Emotion Analysis")

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Dominant Emotion",  facial.get('dominant_emotion', 'N/A').title())
                    col2.metric("Avg Risk Score",     f"{facial.get('avg_risk_score', 0):.4f}")
                    col3.metric("High Risk Frames",   facial.get('high_risk_frames', 0))

                    # Emotion breakdown
                    avg_emotions = facial.get('avg_emotions', {})
                    if avg_emotions:
                        st.subheader("Emotion Breakdown (Average across video)")
                        for emotion, score in sorted(avg_emotions.items(),
                                                     key=lambda x: x[1], reverse=True):
                            st.progress(min(score/100, 1.0),
                                       text=f"{emotion.capitalize()}: {score:.1f}%")

                    # Frame timeline
                    timeline = facial.get('frame_timeline', [])
                    if timeline:
                        st.subheader("📈 Frame Timeline (First 10 samples)")
                        import pandas as pd
                        df = pd.DataFrame(timeline)
                        st.dataframe(df, use_container_width=True)

            else:
                st.error(f"Error: {data.get('detail', data.get('error', 'Video analysis failed'))}")
    else:
        st.markdown("""
        ### 📋 Supported Formats
        | Format | Extension |
        |--------|-----------|
        | MP4 Video | .mp4 |
        | AVI Video | .avi |
        | QuickTime | .mov |
        | Matroska  | .mkv |
        | WebM      | .webm |

        ### 💡 Tips for Best Results
        - Ensure good lighting in the video
        - Face should be clearly visible
        - Shorter videos (< 2 mins) process faster
        - Front-facing camera videos work best
        """)


# ── MULTIMODAL ANALYSIS ──────────────────────────────
elif page == "🔀 Multimodal Analysis":
    st.title("🔀 Multimodal Analysis")
    st.markdown("Combine Text + Facial + Speech for comprehensive risk assessment")
    st.divider()

    text_input = st.text_area("Text input:", height=100,
                               placeholder="Enter text here...")

    col1, col2 = st.columns(2)
    with col1:
        use_webcam = st.checkbox("📷 Include Webcam Analysis", value=True)
    with col2:
        use_mic = st.checkbox("🎤 Include Microphone Analysis", value=False)

    if use_mic:
        duration = st.slider("Recording duration", 3, 15, 5)
    else:
        duration = 5

    st.subheader("Custom Weights (Optional)")
    st.caption("Adjust how much each modality contributes to the final score")
    col1, col2, col3 = st.columns(3)
    with col1:
        text_w = st.slider("Text Weight",   0.0, 1.0, 0.5, 0.1)
    with col2:
        face_w = st.slider("Facial Weight", 0.0, 1.0, 0.3, 0.1)
    with col3:
        speech_w = st.slider("Speech Weight", 0.0, 1.0, 0.2, 0.1)

    total_w = text_w + face_w + speech_w
    if abs(total_w - 1.0) > 0.01:
        st.warning(f"Weights sum to {total_w:.1f} — must equal 1.0. Using defaults.")
        custom_weights = None
    else:
        custom_weights = {"text": text_w, "facial": face_w, "speech": speech_w}

    if st.button("🔀 Run Multimodal Analysis", type="primary"):
        if not text_input:
            st.warning("Please enter some text")
        else:
            payload = {
                "text":           text_input,
                "use_webcam":     use_webcam,
                "use_microphone": use_mic,
                "duration":       duration
            }
            if custom_weights:
                payload['weights'] = custom_weights

            with st.spinner("Running multimodal analysis..."):
                data, code = api_post("/api/predict-multimodal", payload)

            if code == 200 and 'final_risk_score' in data:
                st.divider()
                show_risk(data)
                st.divider()

                st.subheader("Individual Scores")
                scores = data.get('individual_scores', {})
                col1, col2, col3 = st.columns(3)
                with col1:
                    ts = scores.get('text_score')
                    st.metric("Text Score",   f"{ts:.4f}" if ts else "N/A")
                with col2:
                    fs = scores.get('facial_score')
                    st.metric("Facial Score", f"{fs:.4f}" if fs else "N/A")
                with col3:
                    ss = scores.get('speech_score')
                    st.metric("Speech Score", f"{ss:.4f}" if ss else "N/A")

                if 'weights_applied' in data:
                    st.subheader("Weights Applied")
                    wa   = data['weights_applied']
                    cols = st.columns(len(wa))
                    for i, (k, v) in enumerate(wa.items()):
                        cols[i].metric(k.capitalize(), f"{v:.0%}")

                st.divider()
                if text_input:
                    with st.spinner("Generating report..."):
                        pdf_bytes, success = download_report(text_input)
                    if success:
                        st.download_button(
                            label     = "⬇️ Download Full Multimodal Report",
                            data      = pdf_bytes,
                            file_name = "multimodal_risk_report.pdf",
                            mime      = "application/pdf"
                        )
            else:
                st.error(data.get('error', 'Analysis failed'))


# ── MONITORING ───────────────────────────────────────
elif page == "📊 Monitoring":
    st.title("📊 Monitoring Dashboard")
    st.markdown("Real-time drift detection and trend analysis")
    st.divider()

    if st.button("🔄 Refresh"):
        st.rerun()

    data, code = api_get("/api/monitor")

    if code == 200:
        if data.get('status') == 'insufficient_data':
            st.warning(data.get('message', 'Not enough data'))
        else:
            status = data.get('status', 'unknown')
            if status == 'healthy':
                st.success("✅ System Status: HEALTHY")
            else:
                st.warning("⚠️ System Status: WARNING")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Predictions", data.get('total_predictions', 0))
            col2.metric("High Risk Count",   data.get('high_risk_count', 0))
            col3.metric("High Risk Rate",    f"{data.get('high_risk_rate', 0):.1%}")
            col4.metric("Avg Confidence",    f"{data.get('avg_confidence', 0):.1%}")

            st.divider()

            if 'trend_analysis' in data:
                trend = data['trend_analysis']
                st.subheader("Trend Analysis")

                trend_status = trend.get('trend_status', 'NORMAL')
                if trend_status == 'CRITICAL':
                    st.error(f"🚨 Trend Status: {trend_status}")
                elif trend_status == 'WARNING':
                    st.warning(f"⚠️ Trend Status: {trend_status}")
                else:
                    st.success(f"✅ Trend Status: {trend_status}")

                alerts = trend.get('trend_alerts', [])
                if alerts:
                    st.subheader("Active Alerts")
                    for alert in alerts:
                        sev = alert.get('severity', '')
                        if sev == 'CRITICAL':
                            st.error(f"🚨 {alert.get('type')}: {alert.get('message')}")
                        elif sev == 'HIGH':
                            st.warning(f"⚠️ {alert.get('type')}: {alert.get('message')}")
                        else:
                            st.info(f"ℹ️ {alert.get('type')}: {alert.get('message')}")
                else:
                    st.success("No active trend alerts")
    else:
        st.error("Could not fetch monitoring data")


# ── HISTORY ──────────────────────────────────────────
elif page == "📈 History":
    st.title("📈 Prediction History")
    st.markdown("All predictions stored in Supabase PostgreSQL")
    st.divider()

    if st.button("🔄 Refresh History"):
        st.rerun()

    data, code = api_get("/api/history")

    if code == 200 and data.get('success'):
        records = data.get('data', [])
        if records:
            st.success(f"Showing {len(records)} recent predictions")

            import pandas as pd
            df = pd.DataFrame(records)

            if 'alert' in df.columns:
                df['alert'] = df['alert'].map({True: '🚨 YES', False: '✅ NO'})
            if 'confidence' in df.columns:
                df['confidence'] = df['confidence'].apply(lambda x: f"{x:.1%}")

            st.dataframe(df, use_container_width=True)

            st.divider()
            db_stats, _ = api_get("/api/db-stats")
            if db_stats.get('success'):
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Predictions", db_stats.get('total_predictions', 0))
                col2.metric("High Risk Count",   db_stats.get('high_risk_count', 0))
                col3.metric("Alert Count",        db_stats.get('alert_count', 0))
        else:
            st.info("No predictions yet. Run some analyses first!")
    else:
        st.error("Could not fetch history")