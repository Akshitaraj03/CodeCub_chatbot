from sentence_transformers import SentenceTransformer
import faiss
import os
import pickle

# Load sentence transformer model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Read all text files in data/
docs = []
for file in os.listdir("data"):
    with open(f"data/{file}", "r", encoding="utf-8") as f:
        text = f.read()
        chunks = text.split(". ")
        docs.extend(chunks)

# Create embeddings
embeddings = model.encode(docs)

# Create FAISS index
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

# Save index and chunks
faiss.write_index(index, "index.faiss")
with open("chunks.pkl", "wb") as f:
    pickle.dump(docs, f)
