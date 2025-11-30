import streamlit as st
from sentence_transformers import SentenceTransformer

# Load model once — Streamlit will NEVER reload it again
@st.cache_resource
def get_model():
    return SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L3-v2')

embedding_model = get_model()

def get_text_embedding(text: str) -> list[float]:
    """
    Generate an embedding vector for the input text using SentenceTransformer.
    """
    embedding = embedding_model.encode(text)
    return embedding.tolist()
