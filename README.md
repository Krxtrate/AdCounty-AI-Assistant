# 🚀 Enterprise RAG Assistant

An enterprise-grade AI Assistant built using **React, FastAPI, Ollama, ChromaDB, and Retrieval-Augmented Generation (RAG)**.

This project was developed to provide accurate, company-specific responses by combining semantic search, vector databases, local LLM inference, website scraping, and intent-based smalltalk handling.

---

## ✨ Features

### 🧠 Retrieval-Augmented Generation (RAG)

* Website scraping pipeline
* Knowledge ingestion workflow
* Semantic search using vector embeddings
* ChromaDB vector database
* Context-aware response generation
* Reduced hallucinations through retrieval-first architecture

### 🌐 Company Knowledge Assistant

* Answers company-specific questions
* Retrieves information from scraped website content
* Uses company perspective ("we", "our", "us")
* Refuses to invent unavailable company information
* Supports contact information, services, products, careers, and more

### 💬 Smalltalk Engine

* Multi-file JSON intent system
* Instant responses without LLM calls
* Greetings
* Farewells
* Thank-you responses
* Feedback handling
* Casual conversation support

### 🤖 AI Chat

* Powered by Ollama
* Llama 3.1 integration
* Conversation memory
* General knowledge assistance
* Programming and technical support

### 🎨 Image Generation

* Text-to-image generation
* Hugging Face Inference API
* Integrated directly into the chat interface

### ⚡ Modern Frontend

* React-based UI
* Real-time chat experience
* Responsive design
* Clean enterprise-style interface
* Image rendering support

---

# 🏗️ System Architecture

User

↓

React Frontend

↓

FastAPI Backend

├── Smalltalk Intent Engine

├── Company Knowledge Retrieval

│ └── ChromaDB

├── Ollama (Llama 3.1)

└── Image Generation API

---

# 🔄 Data Pipeline

### 1. Website Scraping

Website Content

↓

scrape.py

↓

knowledge/

### 2. Knowledge Processing

knowledge/

↓

ingest.py

↓

Sentence Transformers

↓

ChromaDB

### 3. User Query

User Question

↓

Vector Search

↓

Relevant Context

↓

Llama 3.1

↓

Final Response

---

# 🛠️ Tech Stack

## Frontend

* React
* Axios
* CSS

## Backend

* FastAPI
* Pydantic
* Requests

## AI & NLP

* Ollama
* Llama 3.1
* Sentence Transformers
* Hugging Face Inference API

## Vector Database

* ChromaDB

## Data Processing

* BeautifulSoup
* Website Scraping
* JSON Intent Processing

---

# 📂 Project Structure

```text
Enterprise-RAG-Assistant/
│
├── frontend/
│
├── knowledge/
│   ├── home.txt
│   ├── about.txt
│   ├── services.txt
│   ├── products.txt
│   ├── careers.txt
│   └── contact.txt
│
├── smalltalk/
│   ├── greetings.json
│   ├── thanks.json
│   ├── feedback.json
│   ├── jokes.json
│   └── ...
│
├── scrape.py
├── ingest.py
├── main.py
│
├── .env
├── .gitignore
└── README.md
```

# 🚀 Setup

## Clone Repository

```bash
git clone https://github.com/yourusername/Enterprise-RAG-Assistant.git

cd Enterprise-RAG-Assistant
```

## Install Backend Dependencies

```bash
pip install -r requirements.txt
```

## Install Frontend Dependencies

```bash
cd frontend

npm install
```

## Start Ollama

```bash
ollama run llama3.1:8b
```

## Run Backend

```bash
uvicorn main:app --reload
```

## Run Frontend

```bash
npm run dev
```

---

# 🔄 Updating Company Knowledge

### Scrape Website

```bash
python scrape.py
```

### Generate Embeddings

```bash
python ingest.py
```

### Restart Backend

```bash
uvicorn main:app --reload
```

---

# 💡 Example Queries

### Company Questions

* What services do you offer?
* Tell me about your products.
* How can I contact you?
* Do you offer internships?
* Where is your corporate office located?

### General Questions

* Explain Retrieval-Augmented Generation.
* What is FastAPI?
* Explain vector databases.
* Write a Python sorting algorithm.

### Smalltalk

* Hi
* Thank you
* Bye
* Good morning
* Tell me a joke

### Image Generation

* Generate an image of a futuristic office.
* Create an AI-powered marketing dashboard.
* Generate a digital advertising campaign poster.

---

# 🎯 Future Improvements

* Automatic website recrawling
* Scheduled knowledge refresh
* Source citations
* Authentication & user roles
* Streaming responses
* Hybrid keyword + semantic search
* Analytics dashboard
* Multi-company support

---

# 👨‍💻 Author

**Kritarth**

Built as an enterprise AI assistant project combining modern RAG architecture, vector search, local LLM inference, and intent-based conversational AI.
