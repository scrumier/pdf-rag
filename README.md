# samse-rag

RAG chatbot built for SAMSE, a French building materials distributor.

## What it does

Employees can ask questions in plain French and get answers sourced directly from internal PDF documents. The system finds the relevant passages, then generates a clear response with references to the source files.

## How it works

1. PDFs are parsed and split into chunks with pdfplumber
2. Each chunk is converted to a vector embedding using sentence-transformers
3. Embeddings are stored in ChromaDB, a local vector database
4. At query time, the closest chunks are retrieved and passed to a language model
5. Claude (via OpenRouter) generates a final answer grounded in the retrieved content

## Stack

- Python, Flask
- pdfplumber for PDF extraction
- sentence-transformers for embeddings
- ChromaDB for vector search
- Claude (via OpenRouter) for answer generation

## Context

Built in 2 days as a prototype. Tested on 98 internal PDFs from SAMSE. The goal was to show that a small team can deploy a functional internal knowledge base without fine-tuning any model.

## Author

Sonam — [github.com/scrumier](https://github.com/scrumier)
