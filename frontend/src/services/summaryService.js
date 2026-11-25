import api from "./api";

export async function generateSessionSummary(sessionId, isCompleted = false) {
  const response = await api.post(`/api/summaries/${encodeURIComponent(sessionId)}/generate`, {
    is_completed: isCompleted,
  });
  return response.data;
}

export async function fetchSessionSummary(sessionId) {
  try {
    const response = await api.get(`/api/summaries/${encodeURIComponent(sessionId)}`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function fetchAllSummaries(params = {}) {
  const response = await api.get("/api/summaries", { params });
  return response.data;
}
