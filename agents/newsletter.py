from jinja2 import Environment, FileSystemLoader
import pandas as pd
import os
import chromadb
from sentence_transformers import SentenceTransformer
from langgraph.graph import StateGraph
from typing import TypedDict, Annotated
from typing_extensions import TypedDict
import random

# Configuration
CHROMA_DIR = "data/chroma_db"
COLLECTION_NAME = "stackoverflow_qna"
MODEL_NAME = "all-MiniLM-L6-v2"
TOP_POSTS = 5

# Define state schema
class NewsletterState(TypedDict):
    collection: chromadb.Collection
    model: SentenceTransformer
    posts: list
    newsletter_html: str

def elaborate_solution(solution: str) -> str:
    """Elaborates on the solution with more context and details."""
    # Common elaboration patterns
    elaborations = [
        "This solution addresses the core issue by ",
        "The approach works effectively because ",
        "Key benefits of this solution include ",
        "Implementation considerations: ",
        "Best practices to follow: "
    ]
    
    # Split solution into sentences
    sentences = solution.split('.')
    if not sentences:
        return solution
    
    # Take the first sentence as the main solution
    main_solution = sentences[0].strip()
    
    # Add elaboration
    elaboration = random.choice(elaborations)
    if len(sentences) > 1:
        # Use additional sentences as elaboration
        additional_details = '. '.join(sentences[1:]).strip()
        return f"{main_solution}. {elaboration}{additional_details}"
    else:
        # Generate a simple elaboration if no additional details
        return f"{main_solution}. {elaboration}providing a robust and maintainable approach to the problem."

#  LangGraph-based Newsletter Generation Workflow
class NewsletterGraph(StateGraph):
    def __init__(self):
        super().__init__(state_schema=NewsletterState)

        # Define the workflow steps
        self.add_node("init_components", self.init_components)
        self.add_node("fetch_posts", self.fetch_posts)
        self.add_node("generate_newsletter", self.generate_newsletter)
        self.add_node("save_newsletter", self.save_newsletter)

        # Define the workflow edges (execution order)
        self.add_edge("init_components", "fetch_posts")
        self.add_edge("fetch_posts", "generate_newsletter")
        self.add_edge("generate_newsletter", "save_newsletter")

        # Set the entry point
        self.set_entry_point("init_components")

    def init_components(self, state: NewsletterState) -> NewsletterState:
        """Initializes ChromaDB collection and sentence transformer model."""
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        collection = client.get_collection(COLLECTION_NAME)
        model = SentenceTransformer(MODEL_NAME)
        
        return {
            "collection": collection,
            "model": model,
            "posts": [],
            "newsletter_html": ""
        }

    def fetch_posts(self, state: NewsletterState) -> NewsletterState:
        """Fetches top posts from ChromaDB and formats them for the newsletter."""
        collection = state["collection"]
        
        # Query the collection to get all posts
        results = collection.get()
        
        # Format posts for the newsletter
        all_posts = []
        for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
            # Parse the document content
            title = doc.split('\n')[0].replace('Title: ', '')
            tags = doc.split('\n')[1].replace('Tags: ', '').split(',')
            summary = doc.split('\n')[2].replace('Summary: ', '')
            
            # Format the content in a more natural way
            formatted_title = title.replace('?', '')  # Remove question marks for cleaner titles
            formatted_problem = f"Developers often face challenges with {title.lower()}"
            formatted_solution = elaborate_solution(summary.replace('Summary: ', ''))
            
            # Clean up tags
            cleaned_tags = [tag.strip() for tag in tags if tag.strip()]
            
            # Get category and budget from metadata
            category = metadata.get('category', 'general').replace('_', ' ').title()
            budget = metadata.get('budget', 'unknown').replace('_', ' ').title()
            
            all_posts.append({
                "title": formatted_title,
                "category": category,
                "tags": cleaned_tags,
                "problem": formatted_problem,
                "solution": formatted_solution,
                "budget": budget
            })
        
        # Select top 5 posts randomly (you can modify this to use a different selection criteria)
        selected_posts = random.sample(all_posts, min(TOP_POSTS, len(all_posts)))
        
        return {
            **state,
            "posts": selected_posts
        }

    def generate_newsletter(self, state: NewsletterState) -> NewsletterState:
        """Generates the newsletter HTML using the template."""
        # Load HTML template
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("newsletter_template.html")

        # Render the HTML with dynamic data
        newsletter_html = template.render(posts=state["posts"])

        return {
            **state,
            "newsletter_html": newsletter_html
        }

    def save_newsletter(self, state: NewsletterState) -> NewsletterState:
        """Saves the generated newsletter to a file."""
        # Create output directory if it doesn't exist
        output_dir = "data/output_newsletter"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the rendered newsletter
        output_path = os.path.join(output_dir, "newsletter.html")
        with open(output_path, "w") as f:
            f.write(state["newsletter_html"])

        print(f" Newsletter saved at {output_path}")
        return state

#  Run the newsletter generation workflow
if __name__ == "__main__":
    graph = NewsletterGraph()
    app = graph.compile()
    app.invoke({})  # Pass empty dict as initial state
