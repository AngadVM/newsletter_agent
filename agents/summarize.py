import os
import csv
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain.prompts import PromptTemplate

# Load .env with Azure config
load_dotenv()

# Minimal: Embedding only for querying
embedding = AzureOpenAIEmbeddings(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    openai_api_version=os.getenv("OPENAI_API_VERSION"),
    deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"), 
    model="text-embedding-3-large"
)

# Load vector store with existing embeddings
vectorstore = Chroma(
    collection_name="stackoverflow_qa",
    persist_directory="./chroma_data",
    embedding_function=embedding
)

# Search top 5 relevant docs
query = "python"
docs = vectorstore.similarity_search(query, k=5)
print(f"🔎 Found {len(docs)} matching documents")

# GPT-4o setup for summarization
llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    openai_api_version=os.getenv("OPENAI_API_VERSION"),
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    model_name="gpt-4o"
)

# Prompt for summarizing Q&A sets into an article-style newsletter block
article_prompt = PromptTemplate.from_template("""
You are a tech writer creating a developer newsletter.

You are given 5 StackOverflow Q&A entries. For each, write a brief article-style block summarizing:
- The problem or question
- The accepted solution or approach
- Any helpful insights or tips

Number and format each summary clearly, like:

1. **Question Title**
Summary here...

Q&A Entries:
{text}

Newsletter Summaries:
""")

# Runnable chain
chain = article_prompt | llm

# Extract combined_text from docs
contents = [doc.metadata.get("combined_text", "").strip() for doc in docs if doc.metadata.get("combined_text")]

# Combine into batch input
joined_text = "\n\n".join([f"Q&A #{i+1}:\n{content}" for i, content in enumerate(contents)])

# Run single API call
summary = chain.invoke({"text": joined_text}).content

# Save to CSV for now (HTML or Markdown can be added later)
os.makedirs("data", exist_ok=True)

# Path to save the CSV
csv_path = os.path.join("data", "summary_output.csv")

# Write the summary
with open(csv_path, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Newsletter Summary"])
    writer.writerow([summary])

print(f" Newsletter-style summary saved to {csv_path}")

