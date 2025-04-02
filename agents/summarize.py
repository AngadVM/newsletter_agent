import os
import pandas as pd
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from langgraph.graph import StateGraph
from typing import TypedDict, Annotated
from typing_extensions import TypedDict

#  Load T5-small model (Efficient for CPU)
MODEL_NAME = "t5-small"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

def get_latest_parquet_file(directory="data"):
    """Finds the most recent Parquet file in 'data/' directory."""
    files = [f for f in os.listdir(directory) if f.endswith(".parquet")]
    if not files:
        raise FileNotFoundError(" No Parquet files found in 'data' directory.")
    
    files.sort(key=lambda f: os.path.getmtime(os.path.join(directory, f)), reverse=True)
    latest_file = files[0]
    print(f" Loading data from: {latest_file}")  
    return os.path.join(directory, latest_file)

def load_data():
    """Loads the latest scraped Stack Overflow data."""
    parquet_file = get_latest_parquet_file()
    return pd.read_parquet(parquet_file)

def summarize_text(text):
    """Summarizes a given text using T5-small with detailed solution explanation."""
    # Create a more detailed prompt that encourages comprehensive solution explanation
    prompt = f"""Explain the solution in detail:
    Problem: {text}
    Please provide:
    1. Main solution approach
    2. Key implementation steps
    3. Important considerations
    4. Best practices to follow

    Detailed explanation:"""
    
    inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
    
    # Generate longer output with more tokens
    output = model.generate(
        **inputs,
        max_new_tokens=250,  # Increased from 100 to 250
        num_beams=4,         # Use beam search for better quality
        temperature=0.7,     # Slightly increase creativity
        top_p=0.9,          # Nucleus sampling for better coherence
        do_sample=True      # Enable sampling for more natural text
    )
    
    return tokenizer.decode(output[0], skip_special_tokens=True)

# Define state schema
class SummarizationState(TypedDict):
    df: pd.DataFrame
    summarized_df: pd.DataFrame

#  LangGraph-based Summarization Workflow
class SummarizationGraph(StateGraph):
    def __init__(self):
        super().__init__(state_schema=SummarizationState)

        # Define the workflow steps
        self.add_node("load_data", self.load_data)
        self.add_node("summarize", self.summarize)
        self.add_node("save", self.save)

        # Define the workflow edges (execution order)
        self.add_edge("load_data", "summarize")
        self.add_edge("summarize", "save")

        # Set the entry point
        self.set_entry_point("load_data")

    def load_data(self, state: SummarizationState) -> SummarizationState:
        """Loads Stack Overflow Q&A dataset."""
        df = load_data()
        return {"df": df, "summarized_df": pd.DataFrame()}

    def summarize(self, state: SummarizationState) -> SummarizationState:
        """Summarizes Q&A using T5-small with detailed solutions."""
        df = state["df"]
        summaries = []
        
        for _, row in df.iterrows():
            # Create a more comprehensive input for summarization
            input_text = f"{row['title']}\nProblem: {row.get('problem', row['title'])}\nSolution: {row.get('solution', 'N/A')}"
            summary = summarize_text(input_text)
            
            summaries.append({
                "title": row['title'],
                "tags": row['tags'],
                "problem": row.get('problem', row['title']),
                "solution": row.get('solution', 'N/A'),
                "summary": summary
            })

        summarized_df = pd.DataFrame(summaries)
        return {"df": df, "summarized_df": summarized_df}

    def save(self, state: SummarizationState) -> SummarizationState:
        """Saves summarized data to a Parquet file."""
        output_file = "data/summarized_posts.parquet"
        state["summarized_df"].to_parquet(output_file)
        print(f" Saved summarized data to {output_file}")
        return state

#  Run the summarization workflow
if __name__ == "__main__":
    graph = SummarizationGraph()
    app = graph.compile()
    app.invoke({})  # Pass empty dict as initial state

