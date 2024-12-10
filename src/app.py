import gradio as gr
from src.llm import query_chroma

demo = gr.Interface(
    fn=query_chroma,
    inputs=["text", "slider"],
    outputs=["text"],
)

if __name__ == "__main__":
    demo.launch()
