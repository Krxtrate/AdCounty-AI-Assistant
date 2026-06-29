from chatbot.database import SessionLocal
from chatbot.database.models import Document, Chunk

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

print("\nReading knowledge files...")

db = SessionLocal()
db.query(Chunk).delete()
db.commit()

documents = db.query(Document).all()


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split text into overlapping chunks, respecting line boundaries.
    Overlap carries the last N characters of the previous chunk
    into the next one so context isn't lost at boundaries.
    """
    chunks = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    current = ""

    for line in lines:
        current += line + "\n"

        if len(current) >= chunk_size:
            chunks.append(current.strip())
            # carry overlap forward — last `overlap` chars become start of next chunk
            current = current[-overlap:] if len(current) > overlap else ""

    if current.strip():
        chunks.append(current.strip())

    return chunks


for document in documents:

    text = document.content
    url_lower = document.url.lower()

    print(f"Processing: {document.url}")

    product = None

    if "opsis" in url_lower:
        product = "OpSIS Pro"
    elif "bidcounty" in url_lower:
        product = "BidCounty"
    elif "gam360" in url_lower:
        product = "GAM360"
    elif "isearch" in url_lower:
        product = "iSearchAds"
    elif "genwin" in url_lower:
        product = "GenWin"
    elif "seetv" in url_lower:
        product = "SeeTV"

    chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)

    print(f"  → {len(chunks)} chunks (product={product})")

    for i, chunk in enumerate(chunks):
        db.add(Chunk(
            document_id=document.id,
            chunk_index=i,
            text=chunk,
            product=product,        # None for general pages, product name for product pages
            source=document.source
        ))

    db.commit()

db.close()
print("Chunk ingestion completed successfully!")