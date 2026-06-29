from chatbot.services.chroma import collection

results = collection.get(where={"product": "GenWin"})
docs = results.get("documents", [])
metas = results.get("metadatas", [])

print(f"GenWin chunks in ChromaDB: {len(docs)}\n")
for i, (doc, meta) in enumerate(zip(docs, metas)):
    print(f"--- Chunk {i} ({len(doc)} chars) ---")
    print(doc[:500])
    print()