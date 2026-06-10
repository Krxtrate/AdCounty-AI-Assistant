from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File
from pypdf import PdfReader

from huggingface_hub import InferenceClient
from sentence_transformers import SentenceTransformer

import chromadb
import requests
import base64

from io import BytesIO
from typing import List


# =====================================================
# APP SETUP
# =====================================================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

document_text = ""


# =====================================================
# CHROMADB + EMBEDDINGS
# =====================================================

print("Loading embedding model...")

embedder = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("Connecting to ChromaDB...")

chroma_client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = chroma_client.get_collection(
    name="company_knowledge"
)


# =====================================================
# IMAGE GENERATION CLIENT
# =====================================================

hf_client = InferenceClient(
    api_key="hf_YOURTOKENHERE"
)


# =====================================================
# MODELS
# =====================================================

class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


class ImageRequest(BaseModel):
    prompt: str


# =====================================================
# ROUTES
# =====================================================

@app.get("/")
def home():
    return {
        "message": "AI Assistant Running"
    }


# =====================================================
# CHAT
# =====================================================

@app.post("/generate")
def generate(chat: ChatRequest):

    global document_text

    conversation = ""

    latest_question = chat.messages[-1].content

    # -----------------------------------
    # VECTOR SEARCH
    # -----------------------------------

    query_embedding = embedder.encode(
        latest_question
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )

    print(results["distances"])

    print("\n==============================")
    print("USER QUESTION:")
    print(latest_question)

    print("\nRETRIEVED DOCUMENTS:")

    for doc in results["documents"][0]:
        print("-------------------")
        print(doc)

    print("==============================\n")

    company_context = "\n\n".join(
        results["documents"][0]
    )

    # -----------------------------------
    # SYSTEM PROMPT
    # -----------------------------------

    conversation += f"""
SYSTEM INSTRUCTION:

You are the official AI assistant of TechNova Solutions.

You have direct access to company knowledge.

COMPANY KNOWLEDGE:

{company_context}

IMPORTANT RULES:

1. NEVER say:
   - I don't have access
   - Upload a PDF
   - I cannot access company information
   - I need more information

2. Use the COMPANY KNOWLEDGE section whenever relevant.

3. If the answer exists in COMPANY KNOWLEDGE,
   answer confidently.

4. If the information is not present,
   respond:

   "I couldn't find that information in the company knowledge base."

5. Answer professionally and concisely.

"""

    # -----------------------------------
    # OPTIONAL PDF CONTEXT
    # -----------------------------------

    if document_text:

        conversation += f"""

UPLOADED DOCUMENT:

{document_text[:4000]}

If the user's question refers to the uploaded document,
use this information.

"""

    # -----------------------------------
    # CHAT MEMORY
    # -----------------------------------

    for msg in chat.messages[-10:]:

        if msg.role == "user":

            conversation += (
                f"<|user|>\n"
                f"{msg.content}\n"
            )

        else:

            conversation += (
                f"<|assistant|>\n"
                f"{msg.content}\n"
            )

    conversation += "<|assistant|>\n"

    print("\n===== CONTEXT SENT TO QWEN =====")
    print(company_context[:2000])
    print("================================\n")

    # -----------------------------------
    # OLLAMA
    # -----------------------------------

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:3b",
            "prompt": conversation,
            "stream": False,
            "options": {
                "num_predict": 250,
                "temperature": 0.3
            }
        }
    )

    result = response.json()

    return {
        "output": result["response"]
    }


# =====================================================
# PDF UPLOAD
# =====================================================

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    global document_text

    reader = PdfReader(file.file)

    text = ""

    for page in reader.pages:

        extracted = page.extract_text()

        if extracted:
            text += extracted + "\n"

    document_text = text

    print("\n===== PDF UPLOADED =====")
    print(f"Characters: {len(text)}")
    print("========================\n")

    return {
        "message": "Document uploaded successfully",
        "pdf_length": len(text),
        "pdf_preview": text[:500]
    }


# =====================================================
# IMAGE GENERATION
# =====================================================

@app.post("/generate-image")
def generate_image(data: ImageRequest):

    image = hf_client.text_to_image(
        data.prompt,
        model="black-forest-labs/FLUX.1-schnell"
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="PNG"
    )

    image_base64 = base64.b64encode(
        buffer.getvalue()
    ).decode()

    return {
        "image": image_base64
    }