
import streamlit as st
import uuid

from api_client import send_message


# Application configuration
st.set_page_config(
    page_title="Enterprise AI Assistant",
    page_icon="🤖",
    layout="wide"
)


# Application title
st.title("🤖 Enterprise AI Assistant")

st.caption(
    "Your intelligent enterprise chatbot "
    "powered by Generative AI."
)


# Initialize conversation session
if "session_id" not in st.session_state:

    st.session_state.session_id = str(uuid.uuid4())


# Initialize chat history
if "messages" not in st.session_state:

    st.session_state.messages = []


# Sidebar
with st.sidebar:

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

    # Display user message
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):

        st.markdown(question)


    # Generate assistant response
    with st.chat_message("assistant"):

        with st.spinner("Processing your question..."):

            try:

                result = send_message(
                    question=question,
                    session_id=st.session_state.session_id
                )

                answer = result["answer"]

                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as error:

                st.error(
                    f"Unable to connect with backend: {error}"
                )
