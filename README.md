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

## Installation

```bash
pip install -r requirements.txt
```

## Environment Setup
Create a `.env` file in the root directory with the following variables:

```
# Stackapp API
STACKOVERFLOW_API_KEY=''

# ChromaDB 
CHROMA_HOST="localhost"
CHROMA_PORT="8000"

# SMTP Configuration
SENDGRID_API_KEY=''
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=

# Email credentials
EMAIL_SENDER=sender@gmail.com
EMAIL_PASS= # same as SendGrid API key
EMAIL_RECEIVER=receiver@gmail.com

# Azure OpenAI Credentials
AZURE_OPENAI_API_KEY=''
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT_NAME=
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=
OPENAI_API_VERSION=
```

## Workflow
The project follows a structured pipeline using LangGraph:

1. **Vector ETL Process**
   - Runs the `vector-etl` CLI tool with a configuration file to extract and load data from Stack Overflow into the ChromaDB vector database.
   - Executed through the `run_vector_etl` function.

2. **Newsletter Generation**
   - Uses the `NewsletterGraph` component to generate a newsletter from the processed data.
   - Executed through the `run_newsletter` function.

3. **Email Dispatch**
   - Sends the generated newsletter HTML file to the configured recipients.
   - Uses SendGrid SMTP service for reliable email delivery.
   - Executed through the `run_email_sender` function.

The entire workflow is orchestrated in a LangGraph pipeline where each step is executed sequentially.

---

Contributions are welcome! Feel free to submit issues or pull requests.
