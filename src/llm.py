import chromadb
import pandas as pd
from chromadb.config import Settings
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from sentence_transformers import SentenceTransformer

SYSTEM_PROMPT = """You are an expert in all kinds of anime. 
You provide personalized recommendations based on what the user has already watched and enjoyed. 
Respond only in exact JSON format like this and JSON only:

[
  {
    "anime": "string",
    "reason": "string",
    "score": int,
  }
]

For each recommendation, JSON object keys are defined as follows:
- "anime": The title of the recommended anime.
- "reason": A 20 words explanation of why this anime is being recommended, based on the user's preferences.
- "score": A integer value between 0 and 10, indicating the strength of your recommendation.
- "year": The release year of the recommended anime.
"""


def load_cred() -> None:
    """
    Load credentials from .env file
    """
    ret = load_dotenv()
    assert ret is True


def chroma_db():
    client = chromadb.Client(Settings(persist_directory="data/", is_persistent=True))
    anime_collection = client.create_collection(name="anime_recommendations")

    anime_data = pd.read_csv("data/anime-dataset-2023.csv")
    anime_data = anime_data[
        (~anime_data.Synopsis.str.startswith("No description available"))
        & (~anime_data.Type.isin(["Music"]))
    ].dropna()[["Name", "Synopsis"]]

    anime_data = anime_data.iloc[:1000]

    # Load a pre-trained embedding model
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    # Generate embeddings for anime descriptions
    embeddings = embedding_model.encode(anime_data["Synopsis"].values)

    # Add anime data to the collection
    anime_collection.add(
        ids=[str(i) for i in anime_data.index],  # Unique IDs for each anime
        embeddings=embeddings,  # List of vector embeddings
        metadatas=anime_data[["Name", "Synopsis"]].to_dict(
            orient="records"
        ),  # Metadata as dictionaries
    )


def generate_response(model: str, message: str) -> str:
    """
    Generate response from given model and message
    """
    load_cred()
    client = InferenceClient()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]

    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=500,
    )

    return completion.choices[0].message

def query_chroma():
    client = chromadb.Client(Settings(persist_directory="data/", is_persistent=True))
    anime_collection = client.get_collection(name="anime_recommendations")

    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    # Generate a sample query embedding
    query_embedding = embedding_model.encode("I love action-packed anime with deep storylines, espically Hunter × Hunter.")

    # Search the database
    results = anime_collection.query(
        query_embeddings=[query_embedding],
        n_results=5,  # Number of recommendations to return
        include=["metadatas"]
    )

    # Print recommendations
    for metadata in results['metadatas'][0]:
        print(f"Name: {metadata['Name']}, Synopsis: {metadata['Synopsis']}")

if __name__ == "__main__":
    query_chroma()
