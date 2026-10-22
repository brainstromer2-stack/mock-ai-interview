# AI Mock Interviewer — Live Webcam + Microphone

## Features
- Live browser webcam posture cues using MediaPipe Tasks Vision.
- Browser speech-to-text via Web Speech API (Chrome/Edge recommended).
- Role-based interview questions, saved answers, feedback and downloadable report.
- Optional OpenAI feedback. Without a key, the app uses basic rule-based feedback.
- No PyAudio required. Webcam frames are processed in the browser, not uploaded to Python.

## Deploy
Upload `app.py`, `requirements.txt`, `.gitignore`, `.env.example`, and `README.md` to the root of your GitHub repository. On Streamlit Community Cloud, select the repository and branch, set Main file path to `app.py`, then Deploy.

For OpenAI feedback, open Streamlit app settings → Secrets and add:
`OPENAI_API_KEY = "your-key-here"`
Do not put a real API key in GitHub.

## Browser notes
Allow camera/microphone permissions. Chrome or Edge is recommended. Live posture uses MediaPipe's browser JavaScript package and downloads its model when opened, so CDN/network restrictions may stop it loading. Speech recognition uses the browser Web Speech API and is not supported by all browsers; if unavailable, type the answer instead.

Posture feedback is approximate, not a medical assessment or a definitive measure of interview performance.
