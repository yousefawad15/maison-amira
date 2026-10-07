# Production rules for motion-graphic videos (from the user)

- Do NOT use Higgsfield for motion-graphic videos (voiceover, rendering, sandbox, or generation) unless the user explicitly says so.
- Voiceovers: Google AI Studio (Gemini API TTS), Saudi dialect, female narrator. Key is read from `GEMINI_API_KEY`.
- Transition sounds must be subtle or absent; never loud whooshes.
- The user has auto-accept on: proceed through steps without asking for confirmation.
- Deliver finished videos as files in the chat (SendUserFile), not just links.
