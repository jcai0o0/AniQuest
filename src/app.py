import gradio as gr
from src.llm import query_chroma
from src.reranker_warm import rank_anime_warm
import pandas as pd
from pathlib import Path
import requests

def download_pic(names: list[str]) -> list[str]:
    df = pd.read_csv(str(Path(Path(__file__).parent, "data/final_anime_list.csv")))
    pic_dir = Path(Path(__file__).parent, "data/pics")

    if not pic_dir.exists():
        pic_dir.mkdir(exist_ok=True)

    df = df[df.Name.isin(names)]
    df = df[["Name", "Image URL"]].set_index("Name").reindex(names)

    file_paths = []
    for url in df["Image URL"]:
        file_name = "_".join(url.split("/")[-2:])
        file_path = Path(pic_dir, file_name)

        if file_path.exists():
            file_paths.append(str(file_path))
            continue

        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes

        with open(Path(pic_dir, file_name), 'wb') as file:
            file.write(response.content)
        file_paths.append(str(file_path))

        print(f"Image downloaded successfully: {url}")
    return file_paths
    # return url


def integration_test(query: str, anime_count: int):
    # anime_name_list = query_chroma(query=query, anime_count=anime_count)

    # you need to have the following datasets in src/data/ to call this function
    # 1. warm_rerank_data.csv
    # 2. user_similarities.csv
    # we saved the intermediate matrix for calculation efficiency
    # anime_name_list = rank_anime_warm(userid=12, anime_list=anime_name_list)

    df = pd.read_csv("/Users/janet/PycharmProjects/AniQuest/src/data/final_anime_list.csv")
    import numpy as np
    anime_name_list = np.random.choice(df.Name.values, anime_count)
    anime_pic_list = download_pic(list(anime_name_list))

    return anime_name_list, anime_pic_list

demo = gr.Interface(
    fn=integration_test,
    inputs=["text", "slider"],
    outputs=[gr.Text(label="Anime Name"), gr.Gallery(label="Pictures")],
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0")
