from sentence_transformers import SentenceTransformer
import chromadb

print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("Connecting to ChromaDB...")

client = chromadb.PersistentClient(
    path="./chroma_db"
)

# ==========================================
# DELETE OLD COLLECTION
# ==========================================

try:
    client.delete_collection(
        name="company_knowledge"
    )
    print("Old collection deleted.")
except:
    print("No existing collection found.")

collection = client.get_or_create_collection(
    name="company_knowledge"
)

# ==========================================
# READ COMPANY DATA
# ==========================================

print("Reading company data...")

with open(
    "company_data.txt",
    "r",
    encoding="utf-8"
) as f:

    text = f.read()

# ==========================================
# CHUNKING
# ==========================================

chunks = []
current_chunk = ""

for line in text.splitlines():

    line = line.strip()

    if not line:
        continue

    current_chunk += line + "\n"

    if len(current_chunk) >= 500:
        chunks.append(
            current_chunk.strip()
        )
        current_chunk = ""

if current_chunk:
    chunks.append(
        current_chunk.strip()
    )

print(f"Found {len(chunks)} chunks")

# ==========================================
# STORE EMBEDDINGS
# ==========================================

for i, chunk in enumerate(chunks):

    embedding = model.encode(
        chunk
    ).tolist()

    collection.add(
        ids=[f"chunk_{i}"],
        documents=[chunk],
        embeddings=[embedding]
    )

    print(
        f"Added chunk {i + 1}/{len(chunks)}"
    )

# ==========================================
# VERIFY DATABASE
# ==========================================

print(
    f"\nTotal Chunks Stored: {collection.count()}"
)

print("\nKnowledge base created successfully!")