# CareCloud Voice AI Patient Registration System

An enterprise-ready, voice-activated Patient Intake Coordinator powered by **Google Gemini API**, **Twilio Voice**, and **FastAPI**.

## 📞 Live Test Details

- **Phone Number:** `[YOUR TWILIO NUMBER HERE]`
- **REST API Base URL:** `[YOUR NGROK / HOSTING URL HERE]`

---

## 🏗️ Architecture & Technology Justification

- **Google Gemini API**: Utilized for real-time conversational understanding, tool calling/function execution, and edge-case correction.
- **Twilio Voice & TwiML**: Handles inbound speech recognition (`<Gather speechTimeout="auto">`) and streams responses cleanly back to callers.
- **FastAPI Backend**: Delivers high-performance async REST endpoints adhering to strict envelope formatting `{ "data": ..., "error": ... }`.
- **SQLite Database**: Persistent relational storage with full validation constraint enforcement and soft-delete capabilities.

---

## ⚙️ Quickstart & Local Setup

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```
