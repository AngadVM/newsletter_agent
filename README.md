# 🚀 Newsletter Agent

## Overview
**Newsletter Agent** is an AI-powered automation tool that scrapes Q&A from Stack Overflow, summarizes the content, categorizes it, and generates an article-style newsletter. The final output is sent via email to users.

## Features
- **Scrapes Q&A from Stack Overflow**
- **Summarizes complex discussions into concise insights**
- **Categorizes posts into relevant topics**
- **Stores processed data for future reference and retrieval**
- **Generates an AI-curated newsletter**
- **Automates email delivery to users**

## Workflow
The project follows a structured six-step pipeline:

1. **Scrape Stack Overflow Data**
   - Extracts relevant Q&A using `ScrapingGraph`.

2. **Summarization of Q&A**
   - Processes raw Q&A content into concise, readable summaries using `SummarizationGraph`.

3. **Categorization of Posts**
   - Organizes content into predefined categories using `CategorizationGraph`.

4. **Vector Storage for Future Use**
   - Stores the processed data in a vector database (`VectorStoreGraph`) for efficient retrieval.

5. **Newsletter Generation**
   - Formats the summarized and categorized content into an article using `NewsletterGraph`.

6. **Email Dispatch**
   - Sends the newsletter to users using an SMTP-based email service.


---

Contributions are welcome! Feel free to submit issues or pull requests.

