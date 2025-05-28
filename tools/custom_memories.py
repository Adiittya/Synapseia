import chromadb
from datetime import datetime
import uuid
from .custom_embedding_generate import get_text_embedding

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collections = chroma_client.get_or_create_collection("Synapseia")


def store_memory(text: str, tags: list[str] = None) -> bool:
    """
    Stores memory into chroma db with metadata.
    
    Args:
        text (str): Memory content from Ollama.
        embedding (list[float], optional): Corresponding vector embedding.
        tags (list[str], optional): Tags like "goal", "habit", "user_name".
        
    Returns:
        bool: True if stored successfully, False otherwise.
    """
    try:
        memory_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        metadata = {
            "timestamp": timestamp,
        }
        
        if tags:
            metadata["tags"] = ",".join(tags)
            
        embeddings_to_store = get_text_embedding(text)
        
        collections.add(
            documents=[text],
            embeddings=embeddings_to_store,
            ids=[memory_id],
            metadatas=[metadata],
        )
        
        print(f"[+] Memory stored successfully with ID: {memory_id}")
        return True
        
    except Exception as e:
        print(f"Error while storing memory with error: {e}")
        return False

def search_memory(query:str , n_result: int = 1):
    try:
        query_embedding = get_text_embedding(query)
        results = collections.query(
            query_embeddings=[query_embedding],
            n_results=n_result,
            include=["documents", "metadatas"]
        )
        
        print("Raw query results:", results)  # Debug print
        
        docs = results.get("documents", [])
        metas = results.get("metadatas", [])
        print("Documents:", docs)
        print("Metadatas:", metas)

        final_result = []
        for doc, meta in zip(docs, metas):
            print("Current meta:", meta)
            # If meta is a list, unwrap it
            if isinstance(meta, list) and len(meta) > 0:
                meta = meta[0]

            ts_str = meta.get("timestamp") if isinstance(meta, dict) else None
            if ts_str:
                ts_obj = datetime.fromisoformat(ts_str)
                meta["day_date_time"] = ts_obj.strftime("%A, %Y-%m-%d %H:%M:%S")

            final_result.append({
                "document": doc,
                "metadata": meta
            })

        return final_result

    except Exception as e:
        print(f"Error while querying memories: {e}")
        return None


def get_all_memories():
    try:
        results = collections.get(include=["documents", "metadatas"])

        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        ids = results.get("ids", [])

        final_result = []
        for doc, meta, mem_id in zip(documents, metadatas, ids):
            if isinstance(meta, list) and len(meta) > 0:
                meta = meta[0]

            ts_str = meta.get("timestamp") if isinstance(meta, dict) else None
            if ts_str:
                ts_obj = datetime.fromisoformat(ts_str)
                meta["day_date_time"] = ts_obj.strftime("%A, %Y-%m-%d %H:%M:%S")

            final_result.append({
                "id": mem_id,
                "document": doc,
                "metadata": meta
            })

        return final_result
    except Exception as e:
        print(f"Error while fetching all memories: {e}")
        return []



def delete_memory_by_id(memory_id: str) -> bool:
    """
    Delete a memory from the ChromaDB collection using its ID.

    Args:
        memory_id (str): The unique ID of the memory to delete.

    Returns:
        bool: True if successful, False if any exception occurs.
    """
    try:
        print("")
        collections.delete(ids=[memory_id])
        return True
    except Exception as e:
        print(f"[❌] Failed to delete memory with ID {memory_id}: {e}")
        return False
