import chromadb
import pandas as pd
from sentence_transformers import SentenceTransformer
from langgraph.graph import StateGraph
from typing import TypedDict, Annotated
from typing_extensions import TypedDict

# ChromaDB Configuration
CHROMA_DIR = "data/chroma_db"
COLLECTION_NAME = "stackoverflow_qna"

# Initialize ChromaDB client
def init_chroma():
    """Initialize ChromaDB and create collection."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    # Check if collection exists using the new API
    collections = client.list_collections()
    collection_names = [col.name for col in collections]
    
    if COLLECTION_NAME not in collection_names:
        client.create_collection(COLLECTION_NAME)

    return client.get_collection(COLLECTION_NAME)

# Define state schema
class VectorStoreState(TypedDict):
    df: pd.DataFrame
    collection: chromadb.Collection
    model: SentenceTransformer

# ✅ LangGraph-based Vector Store Workflow
class VectorStoreGraph(StateGraph):
    def __init__(self):
        super().__init__(state_schema=VectorStoreState)

        # Define the workflow steps
        self.add_node("load_data", self.load_data)
        self.add_node("init_components", self.init_components)
        self.add_node("vectorize_and_store", self.vectorize_and_store)

        # Define the workflow edges (execution order)
        self.add_edge("load_data", "init_components")
        self.add_edge("init_components", "vectorize_and_store")

        # Set the entry point
        self.set_entry_point("load_data")

    def load_data(self, state: VectorStoreState) -> VectorStoreState:
        """Loads categorized data from Parquet file."""
        df = pd.read_parquet("data/categorized_posts.parquet")
        return {"df": df, "collection": None, "model": None}

    def init_components(self, state: VectorStoreState) -> VectorStoreState:
        """Initializes ChromaDB collection and sentence transformer model."""
        collection = init_chroma()
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return {
            "df": state["df"],
            "collection": collection,
            "model": model
        }

    def vectorize_and_store(self, state: VectorStoreState) -> VectorStoreState:
        """Vectorizes Q&A data and stores it in ChromaDB."""
        df = state["df"]
        collection = state["collection"]
        model = state["model"]
        
        # Prepare batch data
        documents = []
        metadata = []
        ids = []
        
        for i, row in df.iterrows():
            doc = f"Title: {row['title']}\nTags: {row['tags']}\nSummary: {row['summary']}"
            documents.append(doc)
            metadata.append({"tags": row['tags'], "budget": row['budget']})
            ids.append(str(i))

            # Batch processing to avoid memory overload
            if len(documents) >= 100:
                embeddings = model.encode(documents)
                collection.add(
                    documents=documents,
                    metadatas=metadata,
                    ids=ids,
                    embeddings=embeddings
                )
                documents, metadata, ids = [], [], []
        
        # Store any remaining items
        if documents:
            embeddings = model.encode(documents)
            collection.add(
                documents=documents,
                metadatas=metadata,
                ids=ids,
                embeddings=embeddings
            )

        print("✅ Vectorization and storage completed!")
        return state

# ✅ Run the vector store workflow
if __name__ == "__main__":
    graph = VectorStoreGraph()
    app = graph.compile()
    app.invoke({})  # Pass empty dict as initial state
