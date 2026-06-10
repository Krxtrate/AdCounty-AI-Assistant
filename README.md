# 🤖 AI Assistant with Memory & PDF Chat

A full-stack AI chatbot built using **React**, **FastAPI**, **Ollama**, and **Qwen** that supports:

- 💬 Multi-turn conversations
- 🧠 Context-aware memory
- 📄 PDF document upload
- 📚 Document-based question answering
- ⚡ Local LLM inference (no OpenAI API required)
- 🎨 Modern chat interface

---

## 🚀 Features

### 💬 Conversational Memory
The chatbot remembers previous messages in the current session by maintaining conversation history and sending contextual prompts to the LLM.

Example:

```text
User: My name is Kritarth.
AI: Nice to meet you, Kritarth!

User: What is my name?
AI: Your name is Kritarth.
```

---

### 📄 PDF Upload & Analysis

Upload PDF documents and ask questions about their contents.

Example:

```text
Upload: interview-faq.pdf

Question:
What are some good strengths to mention in an interview?

Answer:
The document suggests leadership, communication, and problem-solving skills.
```

---

### 🖥️ Local LLM Integration

Uses Ollama to run language models locally.

Supported models:

- Qwen 2.5
- Qwen 2.5 Coder
- Phi-3 Mini
- Any Ollama-compatible model

No paid API required.

---

## 🏗️ Tech Stack

### Frontend

- React
- Vite
- Axios
- CSS

### Backend

- FastAPI
- Pydantic
- Requests
- PyPDF

### AI

- Ollama
- Qwen 2.5

---

## 📂 Project Structure

```text
INTERNSHIP/
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   │
│   └── package.json
│
├── main.py
├── .gitignore
└── README.md
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/AI-Assistant-PDF-Chatbot.git
cd AI-Assistant-PDF-Chatbot
```

---

## Backend Setup

Create virtual environment:

```bash
python -m venv venv
```

Activate:

### Windows

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install fastapi uvicorn requests pypdf python-multipart
```

Start FastAPI:

```bash
python -m uvicorn main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

---

## Ollama Setup

Install Ollama:

https://ollama.com

Pull model:

```bash
ollama pull qwen2.5:3b
```

Verify:

```bash
ollama list
```

---

## Frontend Setup

Navigate to frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
npm install axios
```

Start React app:

```bash
npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

---

## API Endpoints

### Health Check

```http
GET /
```

Response:

```json
{
  "message": "Qwen AI API Running"
}
```

---

### Generate Response

```http
POST /generate
```

Request:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "What is Artificial Intelligence?"
    }
  ]
}
```

---

### Upload PDF

```http
POST /upload
```

Upload a PDF document for document-aware responses.

---

## Future Improvements

- Vector Database Integration
- RAG Pipeline
- Chat Persistence
- User Authentication
- Multiple Chat Sessions
- Streaming Responses
- Markdown Rendering
- Syntax Highlighting

---

## Screenshots

### Chat Interface

![Chat UI](screenshots/chat.png)

### PDF Upload

![PDF Upload](screenshots/pdf-upload.png)

---

## Author

**Kritarth**

Built to explore:
- FastAPI
- React
- Local LLMs
- Document Question Answering
- Conversational AI

⭐ Star the repository if you found it useful.
