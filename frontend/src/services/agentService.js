import api from "./api";

/**
 * Send a chat message and prior conversation history to the FastAPI Gemini agent endpoint.
 * Preserves mockAgentService.js separately; never silently falls back to mock replies on error.
 */
export async function sendAgentMessage({
  message,
  sessionId = "default_session",
  history = [],
}) {
  const cleanedMessage = message?.trim();
  if (!cleanedMessage) {
    throw new Error("Please enter or speak a message before sending.");
  }

  const formattedHistory = history
    .filter((item) => item && (item.role === "user" || item.role === "assistant") && item.content?.trim())
    .map((item) => ({
      role: item.role,
      content: item.content.trim(),
    }));

  const requestData = {
    message: cleanedMessage,
    session_id: sessionId,
    history: formattedHistory,
  };

  try {
    const response = await api.post("/api/agent/chat", requestData, {
      timeout: 30000,
    });

    const data = response.data;
    if (!data?.reply) {
      throw new Error("The AI assistant returned an empty response.");
    }

    return {
      id: `assistant-${Date.now()}`,
      role: "assistant",
      content: data.reply,
      timestamp: new Date().toISOString(),
      provider: data.provider || "gemini",
      model: data.model,
      sessionId: data.session_id || sessionId,
      lead: data.lead || null,
      sources: Array.isArray(data.sources) ? data.sources : [],
      sentiment: data.sentiment || null,
      sentimentSummary: data.sentiment_summary || null,
      appointment: data.appointment || null,
    };
  } catch (error) {
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail;
      if (status === 422) {
        throw new Error("Please enter a valid non-empty message.");
      }
      if (typeof detail === "string" && detail.trim()) {
        throw new Error(detail);
      }
      throw new Error("The AI service could not process your request. Please try again.");
    }

    if (error.code === "ECONNABORTED") {
      throw new Error("The request timed out while waiting for the AI assistant.");
    }

    throw new Error(
      "Unable to reach the backend server. Please ensure FastAPI is running on http://127.0.0.1:8001."
    );
  }
}

export async function fetchAgentSession(sessionId) {
  if (!sessionId) return null;
  try {
    const response = await api.get(`/api/agent/session/${encodeURIComponent(sessionId)}`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 404) {
      return null;
    }
    throw error;
  }
}
