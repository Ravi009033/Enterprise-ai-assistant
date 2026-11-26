
import streamlit as st
import uuid
import streamlit.components.v1 as components

from api_client import (
    login_user,
    logout_user,
    get_current_user,
    send_message,
    transcribe_audio,
    generate_speech,
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



def render_live_voice_component(access_token):

    websocket_url = (
        "ws://127.0.0.1:8000/ws/voice"
        f"?token={access_token}"
    )

    html_code = f"""
    <div style="font-family: sans-serif; padding: 10px;">
        <h3>🎙️ Live Voice Assistant</h3>

        <button id="startBtn">Start Live Recording</button>
        <button id="stopBtn" disabled>Stop Recording</button>

        <p id="status">Disconnected</p>
        <div id="transcription"></div>
        <h4>🤖 AI Assistant Response</h4>
        <div id="aiResponse"
           style = "
                white-space: pre-wrap;
                padding: 18px;
                background: #f0f2f6;
                border-radius: 10px;
                font-size: 18px;
                line-height: 1.7;
                min-height: 160px;
                color: #1f2937;
                overflow-wrap: anywhere;
                margin-top: 12px;
            ">
        </div>
    </div>

    <script>
    const wsUrl = "{websocket_url}";

    const startBtn = document.getElementById("startBtn");
    const stopBtn = document.getElementById("stopBtn");
    const status = document.getElementById("status");
    const transcription = document.getElementById("transcription");
    const aiResponse = document.getElementById("aiResponse");

    let socket = null;
    let audioContext = null;
    let mediaStream = null;
    let processor = null;
    let source = null;

    startBtn.onclick = async () => {{

        try {{

            status.textContent = "Connecting...";

            socket = new WebSocket(wsUrl);

            socket.onopen = async () => {{

                try {{

                    mediaStream = await navigator.mediaDevices.getUserMedia({{
                        audio: {{
                            channelCount: 1,
                            echoCancellation: true,
                            noiseSuppression: true
                        }}
                    }});

                    audioContext = new AudioContext({{
                        sampleRate: 16000
                    }});

                    source = audioContext.createMediaStreamSource(mediaStream);

                    processor = audioContext.createScriptProcessor(
                        4096, 1, 1
                    );

                    source.connect(processor);
                    processor.connect(audioContext.destination);

                    processor.onaudioprocess = (event) => {{

                        if (socket.readyState !== WebSocket.OPEN) return;

                        const input = event.inputBuffer.getChannelData(0);
                        const pcm16 = new Int16Array(input.length);

                        for (let i = 0; i < input.length; i++) {{

                            const sample = Math.max(-1, Math.min(1, input[i]));

                            pcm16[i] = sample < 0
                                ? sample * 32768
                                : sample * 32767;
                        }}

                        socket.send(pcm16.buffer);
                    }};

                    status.textContent = "🔴 Recording and streaming audio...";
                    startBtn.disabled = true;
                    stopBtn.disabled = false;

                }} catch (error) {{

                    status.textContent = "Microphone error: " + error.message;

                    socket.close();
                }}
            }};

            socket.onmessage = (event) => {{

                const data = JSON.parse(event.data);

                if (data.type === "connection") {{
                    status.textContent = "Authenticated connection established.";
                }}

                if (data.type === "transcription_ready") {{
                    status.textContent = "🔴 Deepgram ready. Speak now!";
                }}

                if (data.type === "transcription") {{
                    transcription.textContent += data.transcript + " ";
                }}
                if (data.type === "thinking") {{
                    aiResponse.textContent = "⏳ " + data.message;
                }}

                if (data.type === "ai_response") {{
                    aiResponse.textContent = data.answer;
                }}

                if (data.type === "error") {{
                    aiResponse.textContent = "❌ " + data.message;
                }}

                if (data.type === "stream_stopped") {{
                    status.textContent = "Recording stopped.";
                }}
            }};

            socket.onerror = () => {{
                console.error("WebSocket error:", event);
                status.textContent = "WebSocket connection error.";
            }};

            socket.onclose = (event) => {{

                status.textContent =
                    "Disconnected. Code: " + event.code +
                    " Reason: " + (event.reason || "No reason provided");

                console.log("WebSocket closed:", event.code, event.reason);

                startBtn.disabled = false;
                stopBtn.disabled = true;
            }};
        }} catch (error) {{

            status.textContent = "Error: " + error.message;
        }}
    }};

    stopBtn.onclick = () => {{

        if (processor) {{
            processor.disconnect();
            processor = null;
        }}

        if (source) {{
            source.disconnect();
            source = null;
        }}

        if (mediaStream) {{
            mediaStream.getTracks().forEach(track => track.stop());
            mediaStream = null;
        }}

        if (audioContext) {{
            audioContext.close();
            audioContext = null;
        }}

        if (socket && socket.readyState === WebSocket.OPEN) {{
            socket.send("stop");
        }}

        stopBtn.disabled = true;
    }};
    </script>
    """

    components.html(html_code, height=450)



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
st.divider()

render_live_voice_component(
    st.session_state.access_token
)

st.divider()


# Sidebar
with st.sidebar:

    st.header("Account")

    st.write(f"Logged in as: **{st.session_state.username}**")
    st.write(f"Role: {st.session_state.role}")
    st.write(f"Employee ID: {st.session_state.employee_id}")

    st.divider()

    st.subheader("Voice Settings")

    st.checkbox(
        "Enable Voice Response",
        value=True,
        key="voice_response_enabled"
    )

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

        if message.get("audio"):
            st.audio(
                message["audio"],
                format="audio/mpeg"
            )


# User input

# Unified Text + Voice Chat Input
prompt = st.chat_input(
    "Ask a question or record your voice...",
    accept_audio=True,
    audio_sample_rate=16000,
)

# Process text or voice message
if prompt:

    question = prompt.text.strip()

    try:

        # Convert voice to text if audio is recorded
        if prompt.audio is not None:

            with st.spinner("Converting speech to text..."):

                audio_bytes = prompt.audio.getvalue()

                transcription = transcribe_audio(
                    audio_bytes,
                    st.session_state.access_token
                )

                transcript = transcription["transcript"].strip()

            if not question:
                question = transcript
            elif transcript:
                question = question + "\n" + transcript

        if question:

            st.session_state.messages.append({
                "role": "user",
                "content": question
            })

            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):

                with st.spinner("Processing your question..."):

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

            audio_bytes = None
            if st.session_state.get("voice_response_enabled", True):
                try:

                    with st.spinner("Generating voice response..."):

                        audio_bytes = generate_speech(
                            answer,
                            st.session_state.access_token
                        )

                except Exception as audio_error:

                    st.warning(f"Voice generation failed: {audio_error}")

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "audio": audio_bytes
            })


            st.rerun()

        else:
            st.warning("No speech detected. Please try again.")

    except Exception as error:

        st.error(f"Message processing failed: {error}")
