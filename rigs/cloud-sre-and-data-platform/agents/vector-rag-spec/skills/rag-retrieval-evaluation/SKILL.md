---
name: rag-retrieval-evaluation
description: Evaluates hybrid vector search retrieval accuracy, calculating Context Recall and Mean Reciprocal Rank (MRR).
---

# RAG Retrieval Evaluation Procedure

1. Read evaluation query dataset with ground-truth relevant document IDs.
2. Configure hybrid search query: Dense vector embedding + BM25 keyword matching via Reciprocal Rank Fusion (RRF).
3. Execute retrieval queries against Qdrant collection via `mcp-server-qdrant`.
4. Calculate retrieval performance metrics:
   - Hit Rate @ K (K=3, 5, 10).
   - Mean Reciprocal Rank (MRR).
   - Context Precision and Recall.
5. If recall falls below target threshold (> 85%), tune chunk size or HNSW `ef_search` parameter.
6. Commit updated indexing logic and log evaluation benchmark results.
