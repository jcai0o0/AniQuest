import chromadb
import pandas as pd
from chromadb.config import Settings
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from sentence_transformers import SentenceTransformer
from pathlib import Path

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
    client = chromadb.Client(
        Settings(
            persist_directory=str(Path(Path(__file__).parent, "data/")),
            is_persistent=True,
            anonymized_telemetry=False,
        )
    )
    anime_collection = client.create_collection(name="anime_recommendations")
    # TODO: create vector store using final_anime_list.csv
    anime_data = pd.read_csv(
        Path(Path(__file__).parent, "data/", "final_anime_list_cleaned_2nd.csv")
    )
    anime_data = anime_data[
        (~anime_data.Synopsis.str.startswith("No description available"))
    ].dropna()[["title", "Synopsis"]]

    # anime_data = anime_data.iloc[:100]

    # Load a pre-trained embedding model
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    # Generate embeddings for anime descriptions
    embeddings = embedding_model.encode(anime_data["Synopsis"].values)

    # Add anime data to the collection
    anime_collection.add(
        ids=[str(i) for i in anime_data.index],  # Unique IDs for each anime
        embeddings=embeddings,  # List of vector embeddings
        metadatas=anime_data[["title", "Synopsis"]].to_dict(
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


def query_chroma(query: str, anime_count: int) -> list[str]:
    client = chromadb.Client(
        Settings(
            persist_directory=str(Path(Path(__file__).parent, "data/")),
            is_persistent=True,
        )
    )
    anime_collection = client.get_collection(name="anime_recommendations")

    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    # Generate a sample query embedding
    query_embedding = embedding_model.encode(query)

    # Search the database
    results = anime_collection.query(
        query_embeddings=[query_embedding],
        n_results=anime_count,  # Number of recommendations to return
        include=["metadatas"],
    )

    res = []
    # Print recommendations
    for metadata in results["metadatas"][0]:
        # print(f"Name: {metadata['Name']}, Synopsis: {metadata['Synopsis']}")
        res.append(metadata['title'])

    return res


if __name__ == "__main__":
    # chroma_db()
    print(query_chroma(query="I want something like Demon Slayer, but with more romance and produced by Kyoto Animation",
                 anime_count=100))
