"""MeetingAgent — handles audio transcription and speaker diarization."""

from google.adk.agents import Agent

from app.tools import save_meeting_metadata, transcribe_audio_file

_instruction = """
You are MeetingAgent — the audio transcription specialist for WenetBrain.

Your job:
1. Accept an audio file path and meeting metadata.
2. Call `transcribe_audio_file` to get the transcript.
3. Return the transcript along with any metadata.

If the user provides a .txt file next to the audio, it will be used as the transcript.
Otherwise, a mock placeholder is returned (PoC mode).
"""

meeting_agent = Agent(
    name="meeting_agent",
    model="gemini-2.5-flash",
    description="Transcribes meeting audio and returns transcripts.",
    instruction=_instruction,
    tools=[transcribe_audio_file, save_meeting_metadata],
)
