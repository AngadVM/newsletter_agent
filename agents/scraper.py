import requests
import os
import time
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from concurrent.futures import ThreadPoolExecutor, as_completed
from langgraph.graph import StateGraph
from typing import TypedDict, Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configurations
API_KEY = os.getenv("STACK_OVERFLOW_KEY")
BASE_URL = "https://api.stackexchange.com/2.3/questions"
MAX_THREADS = 5  # Use threading for parallel requests
BATCH_SIZE = 100  # Save data in batches
MAX_PAGES = 10    # Max pages to scrape (50 posts per page)

# Define state schema
class ScrapingState(TypedDict):
    df: pd.DataFrame
    current_page: int
    all_posts: list

def fetch_page(page: int, tags: str) -> list:
    """Fetches a single page of Stack Overflow questions."""
    try:
        params = {
            "order": "desc",
            "sort": "activity",
            "site": "stackoverflow",
            "tagged": tags,
            "pagesize": 50,
            "page": page,
            "key": API_KEY
        }

        response = requests.get(BASE_URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("items", [])
        elif response.status_code == 429:
            print(f"Rate limited. Sleeping for 30s...")
            time.sleep(30)
            return []
        else:
            print(f"Failed to fetch page {page}: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching page {page}: {str(e)}")
        return []

def process_posts(posts: list) -> list:
    """Converts API response into structured format."""
    processed = []
    for post in posts:
        processed.append({
            "title": post["title"],
            "link": post["link"],
            "tags": ", ".join(post["tags"]),
            "score": post["score"],
            "is_answered": post["is_answered"],
            "view_count": post["view_count"]
        })
    return processed

def save_to_parquet(posts: list, output_dir: str = "data/") -> str:
    """Saves posts in Parquet format for efficiency."""
    df = pd.DataFrame(posts)

    # Create output directory if not exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Use PyArrow to save in Parquet format
    table = pa.Table.from_pandas(df)
    parquet_file = f"{output_dir}/stackoverflow_{int(time.time())}.parquet"
    pq.write_table(table, parquet_file)

    print(f"Saved {len(posts)} posts to {parquet_file}")
    return parquet_file

# ✅ LangGraph-based Scraping Workflow
class ScrapingGraph(StateGraph):
    def __init__(self):
        super().__init__(state_schema=ScrapingState)

        # Define the workflow steps
        self.add_node("init", self.init)
        self.add_node("scrape", self.scrape)
        self.add_node("save", self.save)

        # Define the workflow edges (execution order)
        self.add_edge("init", "scrape")
        self.add_edge("scrape", "save")

        # Set the entry point
        self.set_entry_point("init")

    def init(self, state: ScrapingState) -> ScrapingState:
        """Initialize the scraping state."""
        return {
            "df": pd.DataFrame(),
            "current_page": 1,
            "all_posts": []
        }

    def scrape(self, state: ScrapingState) -> ScrapingState:
        """Scrape Stack Overflow posts using parallel requests."""
        all_posts = []
        tags = "python;flask"  # You can make this configurable

        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(fetch_page, page, tags) 
                      for page in range(1, MAX_PAGES + 1)]

            for future in as_completed(futures):
                posts = future.result()
                if posts:
                    all_posts.extend(process_posts(posts))

                # Batch save every BATCH_SIZE posts
                if len(all_posts) >= BATCH_SIZE:
                    save_to_parquet(all_posts)
                    all_posts = []

        # Save remaining posts
        if all_posts:
            save_to_parquet(all_posts)

        return {
            **state,
            "all_posts": all_posts,
            "df": pd.DataFrame(all_posts)
        }

    def save(self, state: ScrapingState) -> ScrapingState:
        """Save the final dataset."""
        if not state["df"].empty:
            save_to_parquet(state["all_posts"])
        return state

# Main execution
if __name__ == "__main__":
    graph = ScrapingGraph()
    app = graph.compile()
    app.invoke({})  # Pass empty dict as initial state

