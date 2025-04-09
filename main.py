
import os
from dotenv import load_dotenv
import subprocess
from langgraph.graph import StateGraph
from agents.email_sender import send_email, CONFIG
from agents.newsletter import NewsletterGraph

# Load environment variables
load_dotenv()

def run_vector_etl(state: dict) -> dict:
    print("Running vector-etl CLI...")
    subprocess.run(
        ["vector-etl", "-c", "../config/stackoverflow_to_chroma.yaml"],
        check=True
    )
    print(" vector-etl completed.")
    return state

def run_newsletter(state: dict) -> dict:
    print("Generating newsletter with LangGraph...")
    newsletter_graph = NewsletterGraph()
    newsletter_app = newsletter_graph.compile()
    newsletter_app.invoke({})
    return state

def run_email_sender(state: dict) -> dict:
    print("Sending newsletter email...")
    newsletter_path = "data/output_newsletter/newsletter.html"
    
    if not os.path.exists(newsletter_path):
        raise FileNotFoundError(f"Newsletter file not found at {newsletter_path}")
    
    success = False
    for recipient in CONFIG["recipients"]:
        if send_email(
            recipient=recipient.strip(),
            subject=CONFIG["subject"],
            html_file=newsletter_path
        ):
            success = True
            break

    if not success:
        raise Exception("Failed to send newsletter to any recipient")

    print(" Email sent successfully.")
    return state

def run_pipeline():
    graph = StateGraph(dict)

    graph.add_node("vector_etl", run_vector_etl)
    graph.add_node("newsletter", run_newsletter)
    graph.add_node("send_email", run_email_sender)

    graph.set_entry_point("vector_etl")
    graph.add_edge("vector_etl", "newsletter")
    graph.add_edge("newsletter", "send_email")

    app = graph.compile()
    app.invoke({})

if __name__ == "__main__":
    run_pipeline()

