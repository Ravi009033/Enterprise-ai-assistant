
import streamlit as st
import uuid

from api_client import (
    login_user,
    logout_user,
    get_current_user,
    send_message,
)


# Application configuration
st.set_page_config(
    page_title="Enterprise AI Assistant",
    page_icon="🤖",
    layout="wide"
)


# Initialize authentication state
if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "username" not in st.session_state:
    st.session_state.username = None

if "role" not in st.session_state:
    st.session_state.role = None

if "employee_id" not in st.session_state:
    st.session_state.employee_id = None

# Initialize conversation session
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []


# LOGIN SCREEN
if not st.session_state.access_token:

    st.title("🤖 Enterprise AI Assistant")

    st.subheader("Login")

    with st.form("login_form"):

        username = st.text_input("Username")

        password = st.text_input(
            "Password",
            type="password"
        )

        login_button = st.form_submit_button("Login")

        if login_button:

            if not username or not password:

                st.warning("Please enter username and password.")

            else:

                try:

                    
                    result = login_user(username, password)

                    st.session_state.access_token = result["access_token"]

                    user_data = get_current_user(
                        st.session_state.access_token
                    )

                    st.session_state.username = user_data["username"]
                    st.session_state.role = user_data["role"]
                    st.session_state.employee_id = user_data.get("employee_id")

                    st.success("Login successful!")

                    st.rerun()


                except Exception:

                    st.error(
                        "Login failed. Please check your credentials."
                    )

    st.stop()


# AUTHENTICATED APPLICATION

st.title("🤖 Enterprise AI Assistant")

st.caption(
    "Your intelligent enterprise chatbot "
    "powered by Generative AI."
)


# Sidebar
with st.sidebar:

    st.header("Account")

    st.write(f"Logged in as: **{st.session_state.username}**")
    st.write(f"Role: {st.session_state.role}")
    st.write(f"Employee ID: {st.session_state.employee_id}")

    if st.button("Logout"):

        try:

            logout_user(st.session_state.access_token)

            st.session_state.access_token = None
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())

            st.success("Logged out successfully!")

            st.rerun()

        except Exception as error:

            st.error(f"Logout failed: {error}")

    st.divider()

    st.header("Settings")

    st.write("Enterprise AI Assistant")

    st.caption(
        f"Session: {st.session_state.session_id[:8]}"
    )

    if st.button("Clear Conversation"):

        st.session_state.messages = []

        st.session_state.session_id = str(uuid.uuid4())

        st.rerun()


# Display previous messages
for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# User input
question = st.chat_input(
    "Ask your question here..."
)


# Process user question
if question:

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):

        st.markdown(question)

    with st.chat_message("assistant"):

        with st.spinner("Processing your question..."):

            try:

                conversation_history = [
                    {
                        "role": message["role"],
                        "content": message["content"]
                    }
                    for message in st.session_state.messages[:-1]
                ][-10:]

                result = send_message(
                    question=question,
                    session_id=st.session_state.session_id,
                    access_token=st.session_state.access_token,
                    history=conversation_history
                )

                answer = result["answer"]

                sources = result.get("sources", [])

                if sources:

                    source_text = "\n\n**Sources:**\n"

                    for source in sources:

                        source_text += (
                            f"- [{source['label']}] "
                            f"- {source['filename']} "
                            f"(Page {source['page']})\n"
                        )

                    answer += source_text

                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as error:

                st.error(
                    f"Unable to connect with backend: {error}"
                )
