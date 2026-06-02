# Akira: UAE Real Estate & Land Intelligence Engine 🇦🇪

Akira is a production-grade Hybrid RAG (Retrieval-Augmented Generation) system designed to provide expert-level insights into the Dubai/UAE real estate market. It combines vector search over PDF reports, keyword search over CSV transaction records, and live signals from property web scrapers.

## 🚀 Key Features

*   **Hybrid Retrieval:** Combines Dense (FAISS/SentenceTransformers) and Sparse (BM25) search for maximum accuracy.
*   **Granular Ingestion:** Specialized loaders for large CSV property catalogs (16,000+ records) and PDF market reports.
*   **Intelligence Engine:** Powered by Google's **Gemma-3-1B/4B** models for human-like conversational analysis.
*   **Live Signals:** Integrated "Dorking" bridge to pull recent property signals from SQLite databases.
*   **Production API:** Robust FastAPI backend with session history and query caching.
*   **Dockerized:** Fully containerized setup for consistent deployment.

## 🛠️ Architecture

1.  **Ingestion (`embeddings_builder.py`):** Converts raw files into a FAISS vector index with explicit progress tracking.
2.  **Pipeline (`rag_pipeline.py`):** The core logic for retrieval, prompt engineering, and LLM orchestration.
3.  **API (`akira_api.py`):** Exposes the engine via a RESTful interface for Web/Mobile apps.

## 📦 Setup & Installation

### 1. Environment Configuration
Create a `.env` file in the root directory:
```env
HF_TOKEN=your_huggingface_token_here
QUANTIZE=4bit
LOG_LEVEL=INFO
```

### 2. Run with Docker (Recommended)
```bash
docker compose up -d
```
*The initial startup will take 15-20 minutes to embed the large transaction catalog and download the LLM.*

### 3. Manual Setup (Local Venv)
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python akira_api.py
```

## 🖥️ Usage

### API Endpoint
The API runs on port **8000**.

**Ask a Question:**
```bash
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"query": "What are the latest property trends in Dubai Marina?"}'
```

**Health Check:**
```bash
curl http://localhost:8000/
```

## 📊 Data Management

*   **PDFs:** Place any market reports in the root directory.
*   **CSVs:** Place property transaction files in the root directory.
*   **Auto-Ingest:** The system automatically detects and ingests new files on startup or via the `/ingest` endpoint.

## 📝 Performance Notes
*   **CPU Embedding:** Ingesting 16k+ records takes ~20 mins on a standard CPU. Progress is logged every 500 chunks.
*   **Memory:** The system auto-detects RAM and switches between 1B and 4B models to prevent OOM (Out of Memory) errors.

---
*Built for the next generation of Real Estate Intelligence.*
