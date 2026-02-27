import streamlit as st
import requests
import json
import uuid

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GenAI Course Chatbot",
    page_icon="🎓",
    layout="wide"
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0D1117; }
    .main-title {
        color: #00B4D8;
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        padding: 10px 0;
    }
    .user-msg {
        background-color: #1C2128;
        border-left: 4px solid #00B4D8;
        padding: 10px 15px;
        border-radius: 8px;
        margin: 8px 0;
        color: #E6EDF3;
    }
    .bot-msg {
        background-color: #161B22;
        border-left: 4px solid #02C39A;
        padding: 10px 15px;
        border-radius: 8px;
        margin: 8px 0;
        color: #E6EDF3;
    }
    .confirm-box {
        background-color: #0A1A12;
        border: 2px solid #F4A261;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        color: #E6EDF3;
    }
    .course-card {
        background-color: #1C2128;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ─── API URLs ──────────────────────────────────────────────────────────────────
API_URL     = "http://localhost:8000/chat"
CONFIRM_URL = "http://localhost:8000/resume"

# ─── Session State Init ───────────────────────────────────────────────────────
if "chat_history"     not in st.session_state:
    st.session_state.chat_history     = []
if "messages_display" not in st.session_state:
    st.session_state.messages_display = []
if "enrolled"         not in st.session_state:
    st.session_state.enrolled         = False
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())  # created ONCE — stays same whole session!
    print(f"[Streamlit] New session_id created: {st.session_state.session_id}")
if "waiting_confirm"  not in st.session_state:
    st.session_state.waiting_confirm  = False   # ← True when graph is interrupted
if "confirm_msg"      not in st.session_state:
    st.session_state.confirm_msg      = ""      # ← the confirmation summary text

# ─── Layout ───────────────────────────────────────────────────────────────────
left_col, right_col = st.columns([2, 1])

# ══════════════════════════════════════════════════════════
# LEFT COLUMN — Chat Interface
# ══════════════════════════════════════════════════════════
with left_col:
    st.markdown('<div class="main-title">🎓 GenAI Course Purchase Chatbot</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#8B949E;'>Powered by Groq × LangGraph × FastAPI</p>", unsafe_allow_html=True)
    st.divider()

    # ── Chat History Display ──────────────────────────────
    chat_container = st.container(height=400)
    with chat_container:
        if not st.session_state.messages_display:
            st.markdown("<p style='color:#8B949E; text-align:center;'>👋 Say hi to start chatting!</p>", unsafe_allow_html=True)
        for msg in st.session_state.messages_display:
            if msg["role"] == "user":
                st.markdown(f'<div class="user-msg">👤 <b>You:</b> {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-msg">🤖 <b>CourseBot:</b> {msg["content"]}</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # ⭐ HUMAN IN THE LOOP — YES / NO CONFIRMATION BLOCK
    # ══════════════════════════════════════════════════════
    if st.session_state.waiting_confirm:
        st.markdown("---")
        st.markdown(f"""
        <div class="confirm-box">
            <h4 style="color:#F4A261;">⚠️ Enrollment Confirmation Required!</h4>
            <pre style="color:#E6EDF3; font-size:0.9rem;">{st.session_state.confirm_msg}</pre>
        </div>
        """, unsafe_allow_html=True)

        col_yes, col_no = st.columns(2)

        with col_yes:
            if st.button("✅ YES — Proceed with Enrollment!", use_container_width=True, type="primary"):
                # User clicked YES → resume graph with "yes"
                with st.spinner("Processing your enrollment..."):
                    try:
                        full_response = ""
                        res = requests.post(
                            CONFIRM_URL,
                            json={
                                "session_id":     st.session_state.session_id,
                                "human_response": "yes"   # ← matches app.py
                            },
                            stream=True,
                            timeout=60
                        )
                        for line in res.iter_lines():
                            if line:
                                data = json.loads(line.decode("utf-8"))
                                # ← read both response and resume_done types
                                if data["type"] in ["response", "resume_done"]:
                                    full_response += data.get("content", "")

                        st.session_state.messages_display.append({
                            "role":    "assistant",
                            "content": full_response
                        })
                        st.session_state.waiting_confirm = False
                        st.session_state.confirm_msg     = ""
                        st.session_state.enrolled        = True

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                st.rerun()

        with col_no:
            if st.button("❌ NO — Cancel Enrollment", use_container_width=True):
                # User clicked NO → resume graph with "no"
                with st.spinner("Cancelling..."):
                    try:
                        full_response = ""
                        res = requests.post(
                            CONFIRM_URL,
                            json={
                                "session_id":     st.session_state.session_id,
                                "human_response": "no"    # ← matches app.py
                            },
                            stream=True,
                            timeout=60
                        )
                        for line in res.iter_lines():
                            if line:
                                data = json.loads(line.decode("utf-8"))
                                # ← read both response and resume_done types
                                if data["type"] in ["response", "resume_done"]:
                                    full_response += data.get("content", "")

                        st.session_state.messages_display.append({
                            "role":    "assistant",
                            "content": full_response
                        })
                        st.session_state.waiting_confirm = False
                        st.session_state.confirm_msg     = ""

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                st.rerun()

    # ── Input Box (disabled when waiting for confirmation) ────
    st.markdown("---")
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                "Message",
                placeholder="Type your message here..." if not st.session_state.waiting_confirm else "⚠️ Please confirm enrollment above first!",
                label_visibility="collapsed",
                disabled=st.session_state.waiting_confirm   # ← disabled during confirmation!
            )
        with col2:
            send_btn = st.form_submit_button(
                "Send 🚀",
                use_container_width=True,
                disabled=st.session_state.waiting_confirm   # ← disabled during confirmation!
            )

    # ── Handle Send ───────────────────────────────────────
    if send_btn and user_input.strip() and not st.session_state.waiting_confirm:

        st.session_state.messages_display.append({
            "role":    "user",
            "content": user_input
        })

        try:
            full_response = ""
            payload = {
                "message":      user_input,
                "chat_history": st.session_state.chat_history,
                "session_id":   st.session_state.session_id    # ← send session_id!
            }

            st.markdown("🤖 **CourseBot:**")
            stream_box = st.empty()

            with requests.post(API_URL, json=payload, stream=True, timeout=60) as response:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode("utf-8"))

                        if data["type"] == "response":
                            full_response += data["content"]
                            stream_box.markdown(
                                f'<div class="bot-msg">{full_response}▌</div>',
                                unsafe_allow_html=True
                            )

                        # ⭐ INTERRUPT received — graph paused for human confirmation!
                        elif data["type"] == "interrupt":
                            st.session_state.waiting_confirm = True
                            st.session_state.confirm_msg     = data["content"]
                            print(f"[Streamlit] Interrupt received! Waiting for confirmation.")

                        elif data["type"] == "history_update":
                            st.session_state.chat_history = data["chat_history"]
                            # also save session_id if returned
                            if data.get("session_id"):
                                st.session_state.session_id = data["session_id"]

            # Remove cursor
            if full_response:
                stream_box.markdown(
                    f'<div class="bot-msg">{full_response}</div>',
                    unsafe_allow_html=True
                )

            if full_response:
                st.session_state.messages_display.append({
                    "role":    "assistant",
                    "content": full_response
                })

            if "Enrollment ID" in full_response or "ENR-" in full_response:
                st.session_state.enrolled = True

        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API. Make sure `python app.py` is running on port 8000!")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

        st.rerun()

    # ── Clear Chat ────────────────────────────────────────
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history     = []
        st.session_state.messages_display = []
        st.session_state.enrolled         = False
        st.session_state.waiting_confirm  = False
        st.session_state.confirm_msg      = ""
        st.session_state.session_id = str(uuid.uuid4())  # new session on clear!
        st.rerun()

    if st.session_state.enrolled:
        st.success("🎉 Enrollment Successful! Check your email for confirmation.")

# ══════════════════════════════════════════════════════════
# RIGHT COLUMN — Course Cards + Form
# ══════════════════════════════════════════════════════════
with right_col:

    st.markdown("### 📚 Available Courses")

    courses = [
        {"name": "GenAI for Beginners",            "price": "₹3,999",  "duration": "4 weeks", "color": "#00B4D8"},
        {"name": "Advanced GenAI & Agentic Systems","price": "₹12,499", "duration": "8 weeks", "color": "#7B2FBE"},
        {"name": "LLMOps & DevOps for AI",          "price": "₹8,299",  "duration": "6 weeks", "color": "#02C39A"},
    ]

    for c in courses:
        st.markdown(f"""
        <div class="course-card">
            <p style="color:{c['color']}; font-weight:bold; margin:0;">🔹 {c['name']}</p>
            <p style="color:#8B949E; margin:4px 0; font-size:0.85rem;">
                💰 {c['price']} &nbsp;|&nbsp; ⏱ {c['duration']}
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.markdown("### 📝 Quick Enroll")
    st.markdown("<p style='color:#8B949E; font-size:0.85rem;'>Fill this form or just chat with the bot!</p>", unsafe_allow_html=True)

    with st.form(key="enrollment_form"):
        name          = st.text_input("Full Name",           placeholder="Anjali Mahapatra")
        email         = st.text_input("Email Address",       placeholder="anjali@gmail.com")
        address       = st.text_input("Residential Address", placeholder="Bhubaneswar, Odisha")
        qualification = st.text_input("Qualification",       placeholder="B.Tech Computer Science")
        course        = st.selectbox("Select Course", ["genai_beginner", "genai_advanced", "llmops"])
        submit        = st.form_submit_button("🚀 Enroll Now", use_container_width=True)

    if submit:
        if all([name, email, address, qualification, course]):
            enroll_msg = (
                f"Please enroll me. "
                f"My name is {name}, email is {email}, "
                f"address is {address}, qualification is {qualification}, "
                f"and I want to enroll in {course}."
            )
            try:
                payload = {
                    "message":      enroll_msg,
                    "chat_history": st.session_state.chat_history,
                    "session_id":   st.session_state.session_id
                }
                full_response = ""
                with requests.post(API_URL, json=payload, stream=True, timeout=60) as response:
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line.decode("utf-8"))
                            if data["type"] == "response":
                                full_response += data["content"]
                            elif data["type"] == "interrupt":
                                st.session_state.waiting_confirm = True
                                st.session_state.confirm_msg     = data["content"]
                            elif data["type"] == "history_update":
                                st.session_state.chat_history = data["chat_history"]

                st.session_state.messages_display.append({"role": "user",      "content": f"Enroll me: {name}, {email}, {course}"})
                if full_response:
                    st.session_state.messages_display.append({"role": "assistant", "content": full_response})
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Please fill all fields before enrolling!")