"""
StudyMate AI — Streamlit Frontend
Full-featured study dashboard with chat, summaries, quizzes, flashcards, and study plans.
"""

import streamlit as st
import requests
import io

# ──────────────────────────────────────
# Config
# ──────────────────────────────────────
import os
API_BASE = os.getenv("API_BASE", "http://localhost:8001/api/v1")


st.set_page_config(
    page_title="StudyMate AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────
# Session State Initialization
# ──────────────────────────────────────
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_doc_id" not in st.session_state:
    st.session_state.selected_doc_id = None

# Smart Features session state
if "summary_data" not in st.session_state:
    st.session_state.summary_data = None
if "summary_doc_id" not in st.session_state:
    st.session_state.summary_doc_id = None

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "quiz_doc_id" not in st.session_state:
    st.session_state.quiz_doc_id = None
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}
if "quiz_checked" not in st.session_state:
    st.session_state.quiz_checked = {}

if "flashcards_data" not in st.session_state:
    st.session_state.flashcards_data = None
if "flashcards_doc_id" not in st.session_state:
    st.session_state.flashcards_doc_id = None
if "flashcard_index" not in st.session_state:
    st.session_state.flashcard_index = 0
if "flashcard_reveal" not in st.session_state:
    st.session_state.flashcard_reveal = False

if "study_plan_data" not in st.session_state:
    st.session_state.study_plan_data = None
if "study_plan_doc_id" not in st.session_state:
    st.session_state.study_plan_doc_id = None


# ──────────────────────────────────────
# API Helpers
# ──────────────────────────────────────
def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


def api_post(endpoint, data=None, files=None):
    try:
        kwargs = {"headers": auth_headers()}
        if files:
            kwargs["files"] = files
        else:
            kwargs["json"] = data
        resp = requests.post(f"{API_BASE}{endpoint}", **kwargs, timeout=120)
        return resp
    except requests.ConnectionError:
        st.error("❌ Cannot connect to backend. Is the server running at localhost:8001?")
        return None


def api_get(endpoint):
    try:
        resp = requests.get(f"{API_BASE}{endpoint}", headers=auth_headers(), timeout=30)
        return resp
    except requests.ConnectionError:
        st.error("❌ Cannot connect to backend.")
        return None


def api_delete(endpoint):
    try:
        resp = requests.delete(f"{API_BASE}{endpoint}", headers=auth_headers(), timeout=30)
        return resp
    except requests.ConnectionError:
        st.error("❌ Cannot connect to backend.")
        return None


# ──────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────
st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background: linear-gradient(135deg, #0b091a, #191436, #110e24);
        color: #e2e8f0;
    }

    /* Message Bubbles */
    .user-msg {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        max-width: 85%;
        margin-left: auto;
        word-wrap: break-word;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.2);
    }
    .assistant-msg {
        background: rgba(255, 255, 255, 0.05);
        color: #e2e8f0;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 85%;
        border: 1px solid rgba(255, 255, 255, 0.08);
        word-wrap: break-word;
    }
    .source-badge {
        display: inline-block;
        background: rgba(79, 70, 229, 0.2);
        color: #c7d2fe;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75em;
        margin: 2px 4px 2px 0;
        border: 1px solid rgba(79, 70, 229, 0.3);
    }

    /* Cards and Containers */
    .feature-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin: 12px 0;
    }
    .flashcard-box {
        background: linear-gradient(135deg, #1e1b4b, #311042);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 20px;
        min-height: 220px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 30px;
        margin: 20px 0;
        font-size: 1.4em;
        font-weight: 500;
        color: #f3e8ff;
        cursor: pointer;
        box-shadow: 0 8px 30px rgba(124, 58, 237, 0.15);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: rgba(10, 8, 22, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(255, 255, 255, 0.03);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        color: #94a3b8;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #f1f5f9;
        background-color: rgba(255, 255, 255, 0.05);
    }
    .stTabs [aria-selected="true"] {
        background-color: #4f46e5 !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────
# Auth Screen
# ──────────────────────────────────────
def show_auth():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; margin-top: 50px;'>🎓 StudyMate AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8;'>Your intelligent RAG study companion</p>", unsafe_allow_html=True)
        st.markdown("---")

        tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username or Email", key="login_user")
                password = st.text_input("Password", type="password", key="login_pass")
                submitted = st.form_submit_button("Login", use_container_width=True)

                if submitted:
                    if not username or not password:
                        st.warning("Please fill in all fields.")
                    else:
                        resp = api_post("/auth/login", {"username": username, "password": password})
                        if resp and resp.status_code == 200:
                            data = resp.json()
                            st.session_state.token = data["access_token"]
                            st.session_state.username = username
                            st.success("✅ Login successful!")
                            st.rerun()
                        elif resp:
                            st.error(f"❌ {resp.json().get('detail', 'Login failed')}")

        with tab_register:
            with st.form("register_form"):
                email = st.text_input("Email", key="reg_email")
                username = st.text_input("Username", key="reg_user")
                password = st.text_input("Password", type="password", key="reg_pass")
                submitted = st.form_submit_button("Register", use_container_width=True)

                if submitted:
                    if not email or not username or not password:
                        st.warning("Please fill in all fields.")
                    else:
                        resp = api_post("/auth/register", {
                            "email": email,
                            "username": username,
                            "password": password,
                        })
                        if resp and resp.status_code == 201:
                            st.success("✅ Account created! You can now login.")
                        elif resp:
                            st.error(f"❌ {resp.json().get('detail', 'Registration failed')}")


# ──────────────────────────────────────
# Sidebar
# ──────────────────────────────────────
def show_sidebar():
    with st.sidebar:
        st.markdown(f"### 👋 Hey, **{st.session_state.username}**")
        st.markdown("---")

        # ── Document Upload ──
        st.markdown("#### 📄 Upload Study Document")
        uploaded_file = st.file_uploader(
            "Upload PDF", type=["pdf"], key="pdf_uploader",
            label_visibility="collapsed"
        )
        if uploaded_file:
            with st.spinner("Uploading..."):
                resp = api_post(
                    "/documents/upload",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                )
                if resp and resp.status_code == 201:
                    doc = resp.json()
                    st.success(f"✅ Uploaded: {doc['original_filename']}")

                    # Auto-process
                    with st.spinner("Processing document (chunking + embedding)..."):
                        proc_resp = api_post(f"/documents/{doc['id']}/process")
                        if proc_resp and proc_resp.status_code == 200:
                            proc = proc_resp.json()
                            st.success(
                                f"✅ Processed: {proc['total_chunks']} chunks "
                                f"from {proc['total_pages']} pages"
                            )
                        elif proc_resp:
                            st.warning(f"⚠️ Processing: {proc_resp.json().get('detail', 'failed')}")
                elif resp:
                    st.error(f"❌ Upload: {resp.json().get('detail', 'failed')}")

        # ── Document Selector ──
        st.markdown("#### 📚 Document Context")
        docs_resp = api_get("/documents/")
        if docs_resp and docs_resp.status_code == 200:
            docs = docs_resp.json()["documents"]
            if docs:
                doc_options = {
                    "All Documents": None,
                    **{
                        f"{'✅' if d['status'] == 'processed' else '⏳'} {d['original_filename'][:25]}": d["id"]
                        for d in docs
                    }
                }
                selected = st.selectbox(
                    "Scope:", options=list(doc_options.keys()),
                    key="doc_selector"
                )
                new_doc_id = doc_options[selected]
                # If document selection changed, reset features states
                if new_doc_id != st.session_state.selected_doc_id:
                    st.session_state.selected_doc_id = new_doc_id
                    st.session_state.summary_data = None
                    st.session_state.quiz_data = None
                    st.session_state.flashcards_data = None
                    st.session_state.study_plan_data = None
            else:
                st.info("No documents yet. Upload a PDF above!")
                st.session_state.selected_doc_id = None

        st.markdown("---")

        # ── Conversations ──
        st.markdown("#### 💬 Chat History")
        if st.button("➕ Start New Chat", use_container_width=True):
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.rerun()

        conv_resp = api_get("/conversations")
        if conv_resp and conv_resp.status_code == 200:
            conversations = conv_resp.json()["conversations"]
            for conv in conversations:
                is_active = conv["id"] == st.session_state.conversation_id
                col_btn, col_del = st.columns([5, 1])
                with col_btn:
                    label = f"{'🔵 ' if is_active else ''}{conv['title'][:30]}"
                    if st.button(label, key=f"conv_{conv['id']}", use_container_width=True):
                        load_conversation(conv["id"])
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"del_{conv['id']}"):
                        api_delete(f"/conversations/{conv['id']}")
                        if conv["id"] == st.session_state.conversation_id:
                            st.session_state.conversation_id = None
                            st.session_state.messages = []
                        st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.session_state.summary_data = None
            st.session_state.quiz_data = None
            st.session_state.flashcards_data = None
            st.session_state.study_plan_data = None
            st.rerun()


def load_conversation(conversation_id):
    """Load messages from an existing conversation."""
    resp = api_get(f"/conversations/{conversation_id}")
    if resp and resp.status_code == 200:
        data = resp.json()
        st.session_state.conversation_id = conversation_id
        st.session_state.messages = []
        for msg in data["messages"]:
            entry = {"role": msg["role"], "content": msg["content"]}
            if msg.get("sources"):
                entry["sources"] = msg["sources"]
            st.session_state.messages.append(entry)


# ──────────────────────────────────────
# Chat Tab
# ──────────────────────────────────────
def show_chat_tab():
    # Display messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="🧑‍🎓"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(msg["content"])
                # Show sources
                if msg.get("sources"):
                    sources = msg["sources"]
                    cited = [s for s in sources if s.get("cited_in_answer")]
                    supporting = [s for s in sources if not s.get("cited_in_answer")]

                    if cited:
                        pages_str = ", ".join([f"Page {s['page']}" for s in cited])
                        st.caption(f"📖 **Cited Sources:** {pages_str}")
                    if supporting:
                        pages_str = ", ".join([f"Page {s['page']}" for s in supporting])
                        st.caption(f"📎 **Supporting:** {pages_str}")

    # Empty state
    if not st.session_state.messages:
        st.markdown(
            """
            <div style="text-align: center; padding: 40px 20px; color: #888;">
                <h2 style="color: #6366f1;">💬 Study Assistant Chat</h2>
                <p>Select a document, then ask questions. We'll search your material to answer.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Chat input
    if question := st.chat_input("Ask a question about your documents..."):
        # Show user message immediately
        st.session_state.messages.append({"role": "user", "content": question})
        st.rerun()


# This runs after rerun to handle inputs without breaking display flows
def handle_pending_chat():
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        question = st.session_state.messages[-1]["content"]
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🔍 Searching documents and generating answer..."):
                payload = {
                    "question": question,
                    "document_id": st.session_state.selected_doc_id,
                    "conversation_id": st.session_state.conversation_id,
                }
                resp = api_post("/chat", payload)

                if resp and resp.status_code == 200:
                    data = resp.json()
                    st.session_state.conversation_id = data["conversation_id"]
                    msg_entry = {"role": "assistant", "content": data["answer"]}
                    if data.get("sources"):
                        msg_entry["sources"] = data["sources"]
                    st.session_state.messages.append(msg_entry)
                    st.rerun()
                elif resp:
                    error_detail = resp.json().get("detail", "Unknown error")
                    st.error(f"❌ {error_detail}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"Error: {error_detail}"
                    })
                    st.rerun()


# ──────────────────────────────────────
# Smart Feature Tabs
# ──────────────────────────────────────
def show_summarizer_tab():
    doc_id = st.session_state.selected_doc_id
    if not doc_id:
        st.warning("⚠️ Please select a specific document in the sidebar to generate summaries.")
        return

    # Check if doc changed
    if st.session_state.summary_doc_id != doc_id:
        st.session_state.summary_data = None
        st.session_state.summary_doc_id = doc_id

    if not st.session_state.summary_data:
        if st.button("📝 Generate Summary", use_container_width=True):
            with st.spinner("Summarizing document..."):
                resp = api_post(f"/documents/{doc_id}/summary")
                if resp and resp.status_code == 200:
                    st.session_state.summary_data = resp.json()
                elif resp:
                    st.error(resp.json().get("detail", "Failed to generate summary"))
    else:
        summary = st.session_state.summary_data
        st.markdown(f"### 📋 {summary['title']}")
        st.markdown("---")

        for point in summary["summary_points"]:
            st.markdown(f"💡 {point}")

        st.markdown("---")
        # PDF summary export button
        export_url = f"{API_BASE}/documents/{doc_id}/export-summary"
        try:
            pdf_resp = requests.get(export_url, headers=auth_headers(), timeout=60)
            if pdf_resp.status_code == 200:
                st.download_button(
                    label="📥 Download PDF Summary Report",
                    data=pdf_resp.content,
                    file_name="summary.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.warning("Could not download report generator.")
        except Exception:
            pass


def show_quiz_tab():
    doc_id = st.session_state.selected_doc_id
    if not doc_id:
        st.warning("⚠️ Please select a specific document in the sidebar to generate quizzes.")
        return

    if st.session_state.quiz_doc_id != doc_id:
        st.session_state.quiz_data = None
        st.session_state.quiz_doc_id = doc_id
        st.session_state.quiz_answers = {}
        st.session_state.quiz_checked = {}

    if not st.session_state.quiz_data:
        num_q = st.slider("Number of questions:", min_value=5, max_value=15, value=10)
        if st.button("❓ Generate Practice Quiz", use_container_width=True):
            with st.spinner("Creating practice questions..."):
                resp = api_post(f"/documents/{doc_id}/quiz?num_questions={num_q}")
                if resp and resp.status_code == 200:
                    st.session_state.quiz_data = resp.json()["questions"]
                elif resp:
                    st.error(resp.json().get("detail", "Failed to generate quiz"))
    else:
        st.markdown("### 📝 Practice Quiz")
        st.markdown("Test your understanding of the document.")
        st.markdown("---")

        questions = st.session_state.quiz_data
        correct_count = 0
        total_checked = 0

        for i, q in enumerate(questions):
            st.markdown(f"#### **Q{i+1}:** {q['question']}")

            # Options Selection
            current_choice = st.radio(
                "Select option:",
                q["options"],
                index=st.session_state.quiz_answers.get(i),
                key=f"q_radio_{i}",
                label_visibility="collapsed"
            )

            # Update selected answer index
            if current_choice in q["options"]:
                st.session_state.quiz_answers[i] = q["options"].index(current_choice)

            # Check correctness state
            is_checked = st.session_state.quiz_checked.get(i, False)

            if is_checked:
                user_ans = st.session_state.quiz_answers.get(i)
                correct_ans = q["correct_option"]
                total_checked += 1

                if user_ans == correct_ans:
                    st.success(f"Correct! Index {correct_ans} matches.")
                    correct_count += 1
                else:
                    st.error(f"Incorrect. Correct answer is Option {correct_ans + 1}: **{q['options'][correct_ans]}**")

                st.info(f"💡 **Explanation:** {q['explanation']}")
            else:
                if st.button("Check Answer", key=f"check_btn_{i}"):
                    if st.session_state.quiz_answers.get(i) is None:
                        st.warning("Please select an option first!")
                    else:
                        st.session_state.quiz_checked[i] = True
                        st.rerun()

            st.markdown("---")

        if total_checked > 0:
            st.metric("Score", f"{correct_count} / {len(questions)}", help="Your practice score")

        if st.button("♻️ Reset Quiz", use_container_width=True):
            st.session_state.quiz_data = None
            st.session_state.quiz_answers = {}
            st.session_state.quiz_checked = {}
            st.rerun()


def show_flashcards_tab():
    doc_id = st.session_state.selected_doc_id
    if not doc_id:
        st.warning("⚠️ Please select a specific document in the sidebar to generate flashcards.")
        return

    if st.session_state.flashcards_doc_id != doc_id:
        st.session_state.flashcards_data = None
        st.session_state.flashcards_doc_id = doc_id
        st.session_state.flashcard_index = 0
        st.session_state.flashcard_reveal = False

    if not st.session_state.flashcards_data:
        if st.button("🃏 Generate Flashcards", use_container_width=True):
            with st.spinner("Generating flashcard deck..."):
                resp = api_post(f"/documents/{doc_id}/flashcards")
                if resp and resp.status_code == 200:
                    st.session_state.flashcards_data = resp.json()["flashcards"]
                    st.session_state.flashcard_index = 0
                    st.session_state.flashcard_reveal = False
                elif resp:
                    st.error(resp.json().get("detail", "Failed to generate flashcards"))
    else:
        cards = st.session_state.flashcards_data
        idx = st.session_state.flashcard_index

        st.markdown(f"### 🃏 Interactive Flashcards (Card {idx + 1} of {len(cards)})")
        st.markdown("Click on the card to flip it and reveal the answer.")

        # Display Card
        current_card = cards[idx]
        face_text = current_card["answer"] if st.session_state.flashcard_reveal else current_card["question"]
        face_label = "💡 ANSWER" if st.session_state.flashcard_reveal else "❓ QUESTION"

        # Interactive Clickable Container
        st.markdown(
            f"""
            <div class="flashcard-box">
                <div>
                    <span style="font-size: 0.6em; color: #a78bfa; display: block; margin-bottom: 10px;">{face_label}</span>
                    {face_text}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_left, col_flip, col_right = st.columns([1, 1, 1])

        with col_left:
            if st.button("◀️ Previous", use_container_width=True, disabled=(idx == 0)):
                st.session_state.flashcard_index -= 1
                st.session_state.flashcard_reveal = False
                st.rerun()

        with col_flip:
            if st.button("🔄 Flip Card", use_container_width=True):
                st.session_state.flashcard_reveal = not st.session_state.flashcard_reveal
                st.rerun()

        with col_right:
            if st.button("Next ▶️", use_container_width=True, disabled=(idx == len(cards) - 1)):
                st.session_state.flashcard_index += 1
                st.session_state.flashcard_reveal = False
                st.rerun()

        st.markdown("---")
        if st.button("♻️ Reset Flashcards", use_container_width=True):
            st.session_state.flashcards_data = None
            st.rerun()


def show_study_plan_tab():
    doc_id = st.session_state.selected_doc_id
    if not doc_id:
        st.warning("⚠️ Please select a specific document in the sidebar to generate a study plan.")
        return

    if st.session_state.study_plan_doc_id != doc_id:
        st.session_state.study_plan_data = None
        st.session_state.study_plan_doc_id = doc_id

    if not st.session_state.study_plan_data:
        days = st.slider("Duration (days):", min_value=3, max_value=14, value=7)
        if st.button("📅 Generate Study Schedule", use_container_width=True):
            with st.spinner("Creating study schedule..."):
                resp = api_post(f"/documents/{doc_id}/study-plan?days={days}")
                if resp and resp.status_code == 200:
                    st.session_state.study_plan_data = resp.json()["days"]
                elif resp:
                    st.error(resp.json().get("detail", "Failed to generate study plan"))
    else:
        st.markdown("### 📅 Your Study Schedule")
        st.markdown("Follow this day-by-day checklist to master the material.")
        st.markdown("---")

        days_plan = st.session_state.study_plan_data
        for day in days_plan:
            with st.expander(f"📌 Day {day['day']}: {day['topic']}", expanded=True):
                for task in day["tasks"]:
                    st.markdown(f"- [ ] {task}")

        st.markdown("---")
        if st.button("♻️ Reset Study Plan", use_container_width=True):
            st.session_state.study_plan_data = None
            st.rerun()


# ──────────────────────────────────────
# Main Application Dashboard
# ──────────────────────────────────────
def main():
    if st.session_state.token is None:
        show_auth()
    else:
        show_sidebar()

        # Tabs for main features
        tab_chat, tab_summary, tab_quiz, tab_cards, tab_schedule = st.tabs([
            "💬 Chat Assistant",
            "📝 Summarizer",
            "❓ Quiz Generator",
            "🃏 Flashcards",
            "📅 Study Plan"
        ])

        with tab_chat:
            show_chat_tab()

        with tab_summary:
            show_summarizer_tab()

        with tab_quiz:
            show_quiz_tab()

        with tab_cards:
            show_flashcards_tab()

        with tab_schedule:
            show_study_plan_tab()

        # Handle RAG API request if user posted new chat
        handle_pending_chat()


if __name__ == "__main__":
    main()
