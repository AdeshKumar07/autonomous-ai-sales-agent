import api from "./api";

export async function fetchKnowledgeDocuments() {
  const response = await api.get("/api/knowledge/documents");
  return response.data;
}

export async function fetchKnowledgeStatus() {
  const response = await api.get("/api/knowledge/status");
  return response.data;
}

export async function ingestKnowledgeDocuments(force = false) {
  const response = await api.post("/api/knowledge/ingest", { force });
  return response.data;
}

export async function searchKnowledgeBase(query, topK = 4) {
  const cleaned = query?.trim();
  if (!cleaned) {
    return { query: "", results: [] };
  }
  const response = await api.post("/api/knowledge/search", {
    query: cleaned,
    top_k: topK,
  });
  return response.data;
}
