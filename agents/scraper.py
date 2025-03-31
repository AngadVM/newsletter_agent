import requests
import os
import time
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configurations
API_KEY = os.getenv("STACK_OVERFLOW_KEY")
BASE_URL = "https://api.stackexchange.com/2.3/questions"
MAX_THREADS = 5  # Use threading for parallel requests
BATCH_SIZE = 100  # Save data in batches
MAX_PAGES = 10    # Max pages to scrape (50 posts per page)

# Function to fetch data from Stack Overflow
def fetch_page(page, tags):
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
            print(f"⚠️ Rate limited. Sleeping for 30s...")
            time.sleep(30)
            return []
        else:
            print(f"⚠️ Failed to fetch page {page}: {response.status_code}")
            return []
    except Exception as e:
        print(f"⚠️ Error fetching page {page}: {str(e)}")
        return []

# Function to process posts
def process_posts(posts):
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

# Main scraping function
def scrape_stack_overflow(tags="python;flask", max_pages=MAX_PAGES):
    all_posts = []

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(fetch_page, page, tags) for page in range(1, max_pages + 1)]

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

    print("✅ Scraping completed!")

# Save the scraped data in Parquet format
def save_to_parquet(posts, output_dir="data/"):
    """Saves posts in Parquet format for efficiency."""
    df = pd.DataFrame(posts)

    # Create output directory if not exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Use PyArrow to save in Parquet format
    table = pa.Table.from_pandas(df)
    parquet_file = f"{output_dir}/stackoverflow_{int(time.time())}.parquet"
    pq.write_table(table, parquet_file)

    print(f"✅ Saved {len(posts)} posts to {parquet_file}")

# Main execution
if __name__ == "__main__":
    scrape_stack_overflow(tags="python;flask", max_pages=10)

