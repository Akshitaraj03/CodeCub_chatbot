import os
import fitz
import pandas as pd
import tiktoken
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq 


from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import HumanMessage

# ---- Setup ----
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
tokenizer = tiktoken.get_encoding("p50k_base")

def num_tokens(text):
    return len(tokenizer.encode(text))

def compress_prompt(text, max_tokens=1024):
    tokens = tokenizer.encode(text)
    return tokenizer.decode(tokens[-max_tokens:]) if len(tokens) > max_tokens else text

# ---- Text Extraction ----
def _extract_text(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    raw = ""
    if ext == ".pdf":
        doc = fitz.open(file_path)
        for page in doc:
            raw += page.get_text()
    elif ext == ".csv":
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            for col in df.columns:
                raw += f"{col}: {row[col]}\n"
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()
    return raw

# ---- Vector Store ----
def create_vector_store(uploaded_files):
    documents = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    for file in uploaded_files:
        with open(file.name, "wb") as f:
            f.write(file.getbuffer())
        raw_text = _extract_text(file.name)
        chunks = splitter.create_documents([raw_text])
        documents.extend(chunks)
    vectorstore = FAISS.from_documents(documents, embedding)
    vectorstore.save_local("vector_index")
    return vectorstore

def load_store():
    if os.path.exists("vector_index"):
        return FAISS.load_local("vector_index", embedding, allow_dangerous_deserialization=True)
    return None

# ---- Groq LLM Setup ----
def load_llm():
    return ChatGroq(
        groq_api_key="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",
        model_name="llama3-70b-8192"
    )

# ---- RAG Query ----
def rag_query(query):
    store = load_store()
    if not store:
        return "❌ Vector store not found. Upload documents first."
    compressed = compress_prompt(query, max_tokens=512)
    llm = load_llm()
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=store.as_retriever())
    return qa_chain.run(compressed)

# ---- Summarize Chat ----
def summarize_chat(chat_history):
    llm = load_llm()
    if not chat_history:
        return "❗ No chat history to summarize."
    messages = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
    prompt = f"Summarize the following conversation in bullet points:\n{messages}"
    return llm([HumanMessage(content=prompt)]).content
