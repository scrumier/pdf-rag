# pdf-rag

**Problem:** the answer is somewhere in 300 internal PDFs and nobody knows which one.<br>
**Solution:** ask in plain language, get the answer back with the document it came from.

No fine-tuning, no cloud index. The documents stay on your machine.

## Run it

```bash
cp .env.example .env    # add your OPENROUTER_API_KEY
make setup              # once, downloads the embedding model
make run                # http://127.0.0.1:5050
```

Six demo PDFs are included (supplier contracts, a purchasing procedure, a product catalogue), all fictional, so it answers questions the second it starts. Point `DOCS_PATH` at your own folder to swap them out.

`make test` runs the suite, `make lint` runs Ruff.

## How it works

pdfplumber splits the PDFs into chunks, sentence-transformers turns each chunk into a vector, ChromaDB stores them locally. Your question pulls the closest chunks and Claude answers from those chunks only. That's why it cites instead of inventing.

There's also an MCP server (`rag/mcp_server.py`) if you'd rather query the corpus straight from Claude Desktop or any MCP client.

## What it won't do

It reads text PDFs. Scanned paper needs OCR first. It was built and tested on 98 documents, not on a million.

## This is the level 1

On a folder you fill by hand, it works as is.

In a company the hard part sits elsewhere: the documents live in SharePoint or in a mailbox, not everyone is allowed to see all of them, and nobody wants to run a command to refresh the index. Wiring that up is the real job, and it's the one I do.

[LinkedIn](https://www.linkedin.com/in/sonam-crumiere) · [sonam.me](https://sonam.me)
