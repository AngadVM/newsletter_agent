import os
from dotenv import load_dotenv
from agents.scraper import ScrapingGraph
from agents.summarize import SummarizationGraph
from agents.categorize import CategorizationGraph
from agents.vector_store import VectorStoreGraph
from agents.newsletter import NewsletterGraph
from agents.email_sender import send_email, CONFIG

# Load environment variables
load_dotenv()

def run_pipeline():
    """Execute the full pipeline using LangGraph workflows."""
    try:
        # Step 1: Scrape Stack Overflow
        print("🔄 Step 1: Scraping Stack Overflow...")
        scraping_graph = ScrapingGraph()
        scraping_app = scraping_graph.compile()
        scraping_app.invoke({})

        # Step 2: Summarize Q&A
        print("🔄 Step 2: Summarizing Q&A...")
        summarization_graph = SummarizationGraph()
        summarization_app = summarization_graph.compile()
        summarization_app.invoke({})

        # Step 3: Categorize posts
        print("🔄 Step 3: Categorizing posts...")
        categorization_graph = CategorizationGraph()
        categorization_app = categorization_graph.compile()
        categorization_app.invoke({})

        # Step 4: Vectorize and store
        print("🔄 Step 4: Vectorizing and storing...")
        vector_graph = VectorStoreGraph()
        vector_app = vector_graph.compile()
        vector_app.invoke({})

        # Step 5: Generate Newsletter
        print("🔄 Step 5: Generating newsletter...")
        newsletter_graph = NewsletterGraph()
        newsletter_app = newsletter_graph.compile()
        newsletter_app.invoke({})

        # Step 6: Send Email
        print("🔄 Step 6: Sending newsletter...")
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

        print("✅ Pipeline completed successfully!")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_pipeline()
