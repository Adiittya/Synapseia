from sentence_transformers import SentenceTransformer

# Load model once globally (efficient)
embedding_model = SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L3-v2')

def get_text_embedding(text: str) -> list[float]:
    """
    Generate an embedding vector for the input text using SentenceTransformer.

    Args:
        text (str): Input text to embed.

    Returns:
        list[float]: Embedding vector representing the text.
    """
    embedding = embedding_model.encode(text)
    return embedding.tolist()


