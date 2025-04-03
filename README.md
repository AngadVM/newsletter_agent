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

## Setup and Installation

### Prerequisites
Ensure you have Python 3.8+ installed and set up a Pipenv environment:

```sh
pip install pipenv
pipenv shell
```

### Install Dependencies
```sh
pipenv install
```

### Set Up Environment Variables
Create a `.env` file and configure necessary API keys and email settings:

```env
STACK_OVERFLOW_KEY=''
CHROMA_HOST="localhost"
CHROMA_PORT="8000"
SENDGRID_API_KEY=''

# SMTP Configuration
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=2525

# Email credentials
EMAIL_SENDER=
EMAIL_PASS= (same as sendgrid api key)

EMAIL_RECEIVER=
```

### Running the Pipeline
Execute the pipeline using:

```sh
python main.py
```

## Future Enhancements
- Improve categorization using an AI-based classification model.
- Enhance summarization using fine-tuned LLMs.
- Expand sources beyond Stack Overflow to include relevant tech blogs and forums.
- Implement a web-based management system for newsletters.

---

Contributions are welcome! Feel free to submit issues or pull requests.

