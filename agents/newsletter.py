from jinja2 import Environment, FileSystemLoader
import pandas as pd
import os
import chromadb
from langgraph.graph import StateGraph
from typing_extensions import TypedDict
import random
from langchain_chroma import Chroma
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

# Configuration
CHROMA_DIR = "./chroma_data"
COLLECTION_NAME = "stackoverflow_qa"
TOP_POSTS = 5

# Load environment variables
load_dotenv()

# Define state schema
class NewsletterState(TypedDict):
    vectorstore: Chroma
    llm: AzureChatOpenAI
    posts: list
    newsletter_html: str

# LangGraph-based Newsletter Generator
class NewsletterGraph(StateGraph):
    def __init__(self):
        super().__init__(state_schema=NewsletterState)

        self.add_node("init_components", self.init_components)
        self.add_node("fetch_and_summarize", self.fetch_and_summarize)
        self.add_node("generate_newsletter", self.generate_newsletter)
        self.add_node("save_newsletter", self.save_newsletter)

        self.add_edge("init_components", "fetch_and_summarize")
        self.add_edge("fetch_and_summarize", "generate_newsletter")
        self.add_edge("generate_newsletter", "save_newsletter")

        self.set_entry_point("init_components")

    def init_components(self, state: NewsletterState) -> NewsletterState:
        embedding = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            openai_api_version=os.getenv("OPENAI_API_VERSION"),
            deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"), 
            model="text-embedding-3-large"
        )

        vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=CHROMA_DIR,
            embedding_function=embedding
        )

        llm = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            openai_api_version=os.getenv("OPENAI_API_VERSION"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            model_name="gpt-4o"
        )

        return {
            "vectorstore": vectorstore,
            "llm": llm,
            "posts": [],
            "newsletter_html": ""
        }

    def fetch_and_summarize(self, state: NewsletterState) -> NewsletterState:
        vectorstore = state["vectorstore"]
        llm = state["llm"]

        # Prompt for article-style summaries
        article_prompt = PromptTemplate.from_template("""
        You are a tech writer creating a developer newsletter.

        Given the following StackOverflow question and its accepted answer, write a concise article-style block summarizing:
        - The problem or question
        - The accepted solution or approach
        - Any helpful insights or tips

        Q&A:
        {text}

        Summary:
        """)
        chain = article_prompt | llm

        # Search top 5 posts on a general topic (e.g., "python")
        docs = vectorstore.similarity_search("python", k=TOP_POSTS)
        summaries = []

        for doc in docs:
            content = doc.metadata.get("combined_text", "").strip()
            if not content:
                continue
            try:
                summary = chain.invoke({"text": content}).content.strip()
                summaries.append({
                    "title": content.split("~")[0].replace("Title: ", "").strip(),
                    "summary": summary
                })
            except Exception as e:
                print(f" Error summarizing doc: {e}")

        return {
            **state,
            "posts": summaries
        }

    def generate_newsletter(self, state: NewsletterState) -> NewsletterState:
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("newsletter_template.html")
        html = template.render(posts=state["posts"])
        return {
            **state,
            "newsletter_html": html
        }

    def save_newsletter(self, state: NewsletterState) -> NewsletterState:
        os.makedirs("data/output_newsletter", exist_ok=True)
        path = "data/output_newsletter/newsletter.html"
        with open(path, "w") as f:
            f.write(state["newsletter_html"])
        print(f" Newsletter saved at {path}")
        return state

if __name__ == "__main__":
    graph = NewsletterGraph()
    app = graph.compile()
    app.invoke({})

