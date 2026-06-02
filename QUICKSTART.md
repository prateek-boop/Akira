# ⚡ Akira Quickstart Guide

Follow these steps to get the Akira Real Estate Intelligence Engine running on your machine.

## 1. Prerequisites
- **Docker & Docker Compose** (Recommended)
- **Hugging Face Account** (To get a free `HF_TOKEN`)

## 2. Setup Environment
1. Create a file named `.env` in the project root.
2. Add your Hugging Face token:
   ```env
   HF_TOKEN=your_token_here
   ```

## 3. Launching the Engine (The Easy Way)
The entire system is containerized. To start everything:

```bash
docker compose up -d
```

### What happens next?
- **Downloading Model:** The system will download the Gemma-3 LLM (~2GB).
- **Ingesting Data:** It will automatically scan for `DXB Interact Market Report.pdf` and `transactions-2026-05-03.csv` and build the search index.
- **Ready to Chat:** Check the logs with `docker logs -f akira_chatbot`. When you see **"Akira is online"**, it's ready!

## 4. Testing the API
Once the engine is online, you can ask a question using `curl`:

```bash
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"query": "How are property prices in Dubai Marina?"}'
```

## 📂 Adding Your Own Data
To add new data:
1. Drop your `.pdf` or `.csv` files into the root directory.
2. Restart the container: `docker compose restart`.
3. The system will automatically detect and index the new files!

## 🛠️ Troubleshooting
- **Slow Embedding:** On a CPU, the initial indexing of large CSVs can take 15-20 minutes. Check `docker logs` to see the progress.
- **RAM Issues:** If the container crashes, ensure you have allocated at least 8GB of RAM to Docker.

---
*For more detailed configuration, see the [README.md](./README.md).*
