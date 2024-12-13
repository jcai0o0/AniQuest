import gradio as gr
from src.llm import query_chroma
from src.reranker_warm import rank_anime_warm
import pandas as pd
from pathlib import Path
import requests

css = """
footer {display: none !important}
.gradio-container {
    max-width: 1200px;
    margin: auto;
}
.contain {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 20px;
}
.submit-btn {
    background: linear-gradient(90deg, #4B79A1 0%, #283E51 100%) !important;
    border: none !important;
    color: white !important;
}
.submit-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}
.title {
    text-align: center;
    font-size: 2.5em;
    font-weight: bold;
    margin-bottom: 1em;
    background: linear-gradient(90deg, #4B79A1 0%, #283E51 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.output-image {
    width: 100% !important;
    max-width: 100% !important;
}
"""


def download_pic(names: list[str]):
    df = pd.read_csv(str(Path(Path(__file__).parent, "src/data/final_anime_list.csv")))
    pic_dir = Path(Path(__file__).parent, "src/data/pics")

    if not pic_dir.exists():
        pic_dir.mkdir(exist_ok=True)

    df = df[df.Name.isin(names)]
    df = df[["Name", "Image URL", "Synopsis"]].set_index("Name").reindex(names)
    synopsis_list = df['Synopsis'].tolist()
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
    return file_paths, synopsis_list
    # return url


def integration_warm(query: str):
    anime_name_list = query_chroma(query=query, anime_count=100)

    # you need to have the following datasets in src/data/ to call this function
    # 1. warm_rerank_data.csv
    # 2. user_similarities.csv
    # we saved the intermediate matrix for calculation efficiency
    anime_name_list = rank_anime_warm(userid=12, anime_list=anime_name_list)[:4]
    final_names = [x[0] for x in anime_name_list]

    anime_pic_list, synopsis_list = download_pic(list(final_names))

    return [*anime_name_list, *anime_pic_list, *synopsis_list]




def clear_prompt():
    """Function to clear the prompt box."""
    return ""


def feedback_button(action, anime_name):
    # Store or log feedback (can be expanded to save in a database)
    return f"You {action}d {anime_name}!"


with gr.Blocks(theme=gr.themes.Soft(), css=css) as demo:
    gr.HTML('<div class="title">AniQuest</div>')
    gr.HTML(
        '<div style="text-align: center; margin-bottom: 2em; color: #666; font-size: 24px;">We recommendate animes based on your description</div>')
    gr.HTML("""
                <div style="color: red; margin-bottom: 1em; text-align: center; padding: 10px; background: rgba(255,0,0,0.1); border-radius: 8px;">
                    ⚠️ Welcome, [user_id: 12] to this recommendation system ⚠️
                </div>
            """)

    with gr.Column():
        prompt = gr.Textbox(
            label="Query",
            placeholder="Describe the anime you want to watch next ...",
            lines=1
        )
        with gr.Row():
            generate_btn = gr.Button(
                "🙆 Submit",
                elem_classes=["submit-btn"]
            )
            clear_btn = gr.Button(
                "🙅 Clear",
                elem_classes=["submit-btn"]
            )
    with gr.Row():
        for i in range(4):

            anime_names = []  # Store references to the anime name components
            feedback_texts = []  # List to store feedback components

            with gr.Column(scale=1, elem_classes=["anime-block"]):

                exec(f"anime{i + 1} = gr.Textbox(label='Anime {i + 1}')")

                with gr.Row():  # Add Like and Dislike buttons under each anime name
                    like_btn = gr.Button("👍 Like")
                    dislike_btn = gr.Button("👎 Dislike")

                exec(f"image{i + 1} = gr.Image(label='Image', elem_classes=['output-image', 'fixed-width'])")
                exec(
                    f"description{i + 1} = gr.HTML('<div class=\"anime-description\" style=\"margin-top: 10px; font-size: 14px; color: #666;\">Description for anime {i + 1}</div>')")

                # anime_names.append(anime_name)  # Store the reference to use in the button's click method

                # feedback_text = gr.Textbox(
                #     label="Feedback",
                #     interactive=False,
                #     visible=False  # Hidden initially; becomes visible after feedback
                # )
                # feedback_texts.append(feedback_text)

                # Link Like and Dislike buttons to feedback function
                # like_btn.click(fn=feedback_button, inputs=["Like", anime_name], outputs=feedback_text)
                # dislike_btn.click(fn=feedback_button, inputs=["Dislike", anime_name], outputs=feedback_text)

    generate_btn.click(
        fn=integration_warm,
        inputs=[prompt],
        outputs=[anime1, anime2, anime3, anime4, image1, image2, image3, image4, description1, description2, description3, description4, ]
    )
    # Link the "Clear" button to the clear function to clear the prompt
    clear_btn.click(
        fn=clear_prompt,  # The function to call
        inputs=[],  # No input required
        outputs=[prompt]  # Clears the prompt
    )




if __name__ == "__main__":
    # integration_warm(query='I want something like Demon Slayer, but with more romance and produced by Kyoto Animation')
    # warm user
    demo.launch(server_name="0.0.0.0", server_port=7860)
