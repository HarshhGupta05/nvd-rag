from langchain_huggingface import HuggingFaceEmbeddings
import torch
from src.core.config import settings

def get_embedding_model():
    # return HuggingFaceEmbeddings(model_name=settings.embedding_model)

# this service is abstracted to allow for easy swapping of embedding models in the future, if needed.
# configuring for available GPUs 

    if torch.cuda.is_available():
        device = "cuda"
        print("[INFO] GPU acceleration enabled (CUDA).")
    elif torch.backends.mps.is_available():
        device = "mps"
        print("[INFO] GPU acceleration enabled (Apple MPS).")
    else:
        device = "cpu"
        print("[WARNING] No GPU detected. Defaulting to CPU inference.")
            
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={'device': device},
        encode_kwargs={'normalize_embeddings': False}
)