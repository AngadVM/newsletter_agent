import pandas as pd
import re
from langgraph.graph import StateGraph
from typing import TypedDict, Annotated
from typing_extensions import TypedDict

# Keyword-based budget categories
BUDGET_KEYWORDS = {
    "low_budget": ["free", "open-source", "cheap", "affordable"],
    "mid_budget": ["paid", "license", "subscription"],
    "high_budget": ["enterprise", "premium", "expensive"]
}

# Rule-based categorization
def categorize_budget(tags, title, solution):
    """Categorize based on keywords and tags."""
    content = f"{tags} {title} {solution}".lower()
    
    for budget, keywords in BUDGET_KEYWORDS.items():
        if any(word in content for word in keywords):
            return budget
    
    return "unknown"

# Categorizing tags
def categorize_tags(tags):
    """Categorize into technology-specific tags."""
    tech_tags = {
        "python": ["python", "flask", "django", "pandas"],
        "javascript": ["javascript", "node.js", "react", "vue"],
        "databases": ["sql", "mysql", "postgresql", "mongodb"],
        "ai_ml": ["machine-learning", "ai", "nlp", "transformer"],
    }

    for category, keywords in tech_tags.items():
        if any(tag in tags for tag in keywords):
            return category

    return "other"

# Define state schema
class CategorizationState(TypedDict):
    df: pd.DataFrame
    categorized_df: pd.DataFrame

# ✅ LangGraph-based Categorization Workflow
class CategorizationGraph(StateGraph):
    def __init__(self):
        super().__init__(state_schema=CategorizationState)

        # Define the workflow steps
        self.add_node("load_data", self.load_data)
        self.add_node("categorize", self.categorize)
        self.add_node("save", self.save)

        # Define the workflow edges (execution order)
        self.add_edge("load_data", "categorize")
        self.add_edge("categorize", "save")

        # Set the entry point
        self.set_entry_point("load_data")

    def load_data(self, state: CategorizationState) -> CategorizationState:
        """Loads summarized Stack Overflow data."""
        df = pd.read_parquet("data/summarized_posts.parquet")
        return {"df": df, "categorized_df": pd.DataFrame()}

    def categorize(self, state: CategorizationState) -> CategorizationState:
        """Categorizes posts into budgets and tags."""
        df = state["df"]
        
        # Apply categorization
        df["budget"] = df.apply(lambda row: categorize_budget(row["tags"], row["title"], row["solution"]), axis=1)
        df["category"] = df["tags"].apply(categorize_tags)
        
        return {"df": df, "categorized_df": df}

    def save(self, state: CategorizationState) -> CategorizationState:
        """Saves categorized data to a Parquet file."""
        output_file = "data/categorized_posts.parquet"
        state["categorized_df"].to_parquet(output_file)
        print(f"✅ Categorized data saved to {output_file}")
        return state

# ✅ Run the categorization workflow
if __name__ == "__main__":
    graph = CategorizationGraph()
    app = graph.compile()
    app.invoke({})  # Pass empty dict as initial state

