
from deepgram import DeepgramClient
from backend.app.config import settings
import re
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
from deepgram.listen.v1.types import ListenV1Results
import asyncio
from contextlib import asynccontextmanager


def get_deepgram_client():
    """
    Create and return a Deepgram client.
    """
    return DeepgramClient(
        api_key=settings.deepgram_api_key
    )


def speech_to_text(audio_bytes: bytes) -> str:
    """
    Convert recorded audio bytes into text using Deepgram.
    """

    if not audio_bytes:
        raise ValueError("Audio data is empty.")

    client = get_deepgram_client()

    response = client.listen.v1.media.transcribe_file(
        request=audio_bytes,
        model="nova-3",
        language="multi",
        smart_format=True,
    )

    transcript = (
        response.results
        .channels[0]
        .alternatives[0]
        .transcript
    )

    return transcript.strip()



def clean_text_for_speech(text: str) -> str:
    """Remove Markdown formatting and source references before TTS."""

    # Remove source section
    text = re.split(r"\n\s*\*\*Sources:\*\*", text, flags=re.IGNORECASE)[0]

    # Remove Markdown links but keep their visible text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove Markdown formatting
    text = re.sub(r"(\*\*|__|\*|_|~~|`)", "", text)

    # Remove heading markers
    text = re.sub(r"(?m)^\s*#{1,6}\s*", "", text)

    # Clean extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text



def text_to_speech(text: str) -> bytes:
    """
    Convert long text into speech using Deepgram.
    Splits text into chunks of at most 1800 characters.
    """

    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    text = clean_text_for_speech(text)

    client = get_deepgram_client()

    max_chars = 1800

    # Split text at sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    chunks = []
    current_chunk = ""

    for sentence in sentences:

        if len(sentence) > max_chars:

            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            # Split unusually long sentences safely
            for i in range(0, len(sentence), max_chars):
                chunks.append(sentence[i:i + max_chars])

            continue

        candidate = (
            current_chunk + " " + sentence
            if current_chunk
            else sentence
        )

        if len(candidate) <= max_chars:
            current_chunk = candidate
        else:
            chunks.append(current_chunk)
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    # Generate audio for every chunk
    audio_parts = []

    for chunk in chunks:

        response = client.speak.v1.audio.generate(
            text=chunk,
            model="aura-2-thalia-en",
        )

        audio_parts.append(b"".join(response))

    audio_bytes = b"".join(audio_parts)

    if not audio_bytes:
        raise ValueError("Audio generation failed.")

    return audio_bytes


def get_async_deepgram_client():
    return AsyncDeepgramClient(
        api_key=settings.deepgram_api_key
    )


def get_live_transcription_connection():

    client = get_async_deepgram_client()

    connection = client.listen.v1.connect(
        model="nova-3",
        encoding="linear16",
        sample_rate="16000",
        channels="1",
        language="multi",
        interim_results="true",
        smart_format="true",
        punctuate="true",
    )

    return client, connection



def register_transcription_events(
    connection,
    websocket,
    on_final_transcript=None,
):

    final_segments = []

    def handle_message(message):

        if isinstance(message, ListenV1Results):

            if message.channel and message.channel.alternatives:

                transcript = (
                    message.channel.alternatives[0].transcript
                )

                if transcript and transcript.strip():

                    # Send transcription to browser.
                    asyncio.create_task(
                        websocket.send_json({
                            "type": "transcription",
                            "transcript": transcript,
                            "is_final": message.is_final,
                            "speech_final": message.speech_final,
                        })
                    )

                    # Collect completed transcription segments.
                    if message.is_final:
                        final_segments.append(transcript.strip())

                    # Process complete spoken sentence.
                    if message.speech_final:

                        complete_transcript = " ".join(
                            final_segments
                        ).strip()

                        final_segments.clear()

                        if complete_transcript and on_final_transcript:

                            asyncio.create_task(
                                on_final_transcript(
                                    complete_transcript
                                )
                            )

    connection.on(
        EventType.MESSAGE,
        handle_message
    )


@asynccontextmanager
async def live_transcription_session(websocket,  on_final_transcript=None,):

    client, context = get_live_transcription_connection()

    async with context as connection:

        register_transcription_events(
            connection,
            websocket,
            on_final_transcript,
        )

        listener = asyncio.create_task(
            connection.start_listening()
        )

        try:
            yield connection

        finally:
            if not listener.done():
                await connection.send_close_stream()

            await listener