from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File
from pypdf import PdfReader
from dotenv import load_dotenv

from huggingface_hub import InferenceClient
from sentence_transformers import SentenceTransformer

import chromadb
import requests
import base64
import os

from io import BytesIO
from typing import List

load_dotenv()

from huggingface_hub import login

hf_token = os.getenv("hftoken")

if hf_token:
    login(token=hf_token)

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

collection = chroma_client.get_or_create_collection(
    name="company_knowledge"
)


# =====================================================
# IMAGE GENERATION CLIENT
# =====================================================

hf_client = InferenceClient(
    api_key=os.getenv("hftoken")
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

    if not chat.messages:
        return {
            "output": "No message received."
        }

    latest_question = ""

    for msg in chat.messages[-3:]:
        if msg.role == "user":
            latest_question += msg.content + " "

    latest_question_lower = latest_question.lower()

    company_keywords = [
        "adcounty",
        "company",
        "service",
        "services",
        "product",
        "products",
        "support",
        "employee",
        "employees",
        "client",
        "clients",
        "internship",
        "internships",
        "technology",
        "technologies",
        "contact",
        "office",
        "headquarters",
        "policy",
        "policies"
    ]

    is_company_question = any(
        keyword in latest_question_lower
        for keyword in company_keywords
    )

    # -----------------------------------
    # VECTOR SEARCH
    # -----------------------------------

    company_context = ""

    if is_company_question:

        query_embedding = embedder.encode(
            latest_question
        ).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )

        print("\nDISTANCES:")
        print(results["distances"])

        retrieved_docs = results.get(
            "documents",
            [[]]
        )[0]

        company_context = "\n\n".join(
            retrieved_docs
        )[:6000]

        if not company_context.strip():
            company_context = "No relevant company information found."

    else:

        print("\nGENERAL CHAT DETECTED")

    print("\n==============================")
    print("USER QUESTION:")
    print(latest_question)

    if is_company_question:

        print("\nRETRIEVED DOCUMENTS:")

        for doc in results["documents"][0]:
            print("-------------------")
            print(doc[:300])

    print("==============================\n")

    # -----------------------------------
    # SYSTEM PROMPT
    # -----------------------------------

    conversation += f"""

    SYSTEM INSTRUCTION:

    You are the official AI assistant of AdCounty Media.

    COMPANY KNOWLEDGE:

    {company_context}

    RULES:

    1. If the user asks about AdCounty Media,
    use COMPANY KNOWLEDGE as the primary source.

    2. If the answer is present in COMPANY KNOWLEDGE,
    answer using that information.

    3. If the user asks about AdCounty Media and the
    information is not available in COMPANY KNOWLEDGE,
    respond:

    "Sorry, I couldn't find that information."

    4. If the user asks a general question unrelated
    to AdCounty Media, answer normally as a helpful,
    intelligent AI assistant.

    5. You may:
    - Explain concepts
    - Answer technical questions
    - Help with coding
    - Tell jokes
    - Engage in conversation
    - Assist with learning

    6. Never invent company-specific information.

    7. Answer completely and do not omit items from lists.

    8. If company information is available, answer naturally.

        Never mention:
        - COMPANY KNOWLEDGE
        - knowledge base
        - retrieved documents
        - context
        - database

        Present company information as normal factual information.

        If information is unavailable, respond only:

        "Sorry, I couldn't find that information."

        Do not explain why.
        Do not mention missing context.

    9. Never list information that is unavailable.
        
        If a field is unknown, omit it entirely.

        Do not say:
        - Not specified
        - Not available
        - Not found
        - Missing

        Simply exclude unavailable information from the answer.

    10. When answering broad questions such as:

        - Complete overview
        - Tell me about the company
        - Summarize the company

        Provide a concise summary rather than repeating every detail.

        Prioritize:

        1. Company description
        2. Services
        3. Products
        4. Technologies
        5. Policies
        6. Contact information

        Keep summaries under 300 words.
    """

    # -----------------------------------
    # OPTIONAL PDF CONTEXT
    # -----------------------------------

    if document_text:

        conversation += f"""

        UPLOADED DOCUMENT:

        {document_text[:2500]}

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

    print("\n===== CONTEXT SENT TO LLAMA =====")
    print(company_context[:2000])
    print("================================\n")

    # -----------------------------------
    # OLLAMA
    # -----------------------------------

    payload = {
        "model": "llama3.1:8b",
        "prompt": conversation,
        "stream": False,
        "options": {
            "num_predict": 350,
            "temperature": 0.2
        }
    }

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=120
        )

        if response.status_code != 200:
            return {
                "output": "The AI service is currently unavailable."
            }

    except requests.exceptions.RequestException:
        return {
            "output": "The AI service is currently unavailable."
        }
        
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

    try:
        image = hf_client.text_to_image(
            data.prompt,
            model="black-forest-labs/FLUX.1-schnell"
        )

    except Exception:
        return {
            "image": None,
            "error": "Image generation failed."
        }

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