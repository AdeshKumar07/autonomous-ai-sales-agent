/**
 * Simulated AI Sales Representative service.
 *
 * NOTE: This is a mock client-side response generator for UI and voice flow
 * development. It is intentionally separated from UI components so it can later
 * be swapped with:
 *   POST http://127.0.0.1:8001/api/agent/chat (via src/services/api.js)
 */

// Future backend integration reference (do not call until endpoint is implemented):
// import api from "./api";
// export async function fetchAgentResponse({ message, history, language }) {
//   const response = await api.post("/api/agent/chat", { message, history, language });
//   return response.data;
// }

function buildSalesReply(userMessage) {
  const normalized = userMessage.toLowerCase().trim();

  if (
    normalized.includes("product") ||
    normalized.includes("feature") ||
    normalized.includes("solution") ||
    normalized.includes("platform") ||
    normalized.includes("service")
  ) {
    return (
      "Our Autonomous AI Sales Platform helps teams qualify inbound leads, answer customer questions using your knowledge base, and book discovery calls automatically. " +
      "Would you like to hear how it integrates with your existing CRM workflow?"
    );
  }

  if (
    normalized.includes("price") ||
    normalized.includes("pricing") ||
    normalized.includes("cost") ||
    normalized.includes("plan") ||
    normalized.includes("quote") ||
    normalized.includes("budget")
  ) {
    return (
      "Our pricing depends on your team size, call volume, and CRM integration requirements. " +
      "A sales representative can prepare a customized quotation for you. Roughly how many leads or conversations does your team handle each month?"
    );
  }

  if (
    normalized.includes("demo") ||
    normalized.includes("schedule") ||
    normalized.includes("appointment") ||
    normalized.includes("meeting") ||
    normalized.includes("book")
  ) {
    return (
      "I would be happy to help schedule a live product demo with our team. " +
      "What date and time works best for you, and which time zone are you in?"
    );
  }

  if (
    normalized.includes("interested") ||
    normalized.includes("sign up") ||
    normalized.includes("get started") ||
    normalized.includes("buy") ||
    normalized.includes("trial")
  ) {
    return (
      "That's great to hear! To recommend the right setup, could you share a bit about your business requirements—such as your industry, team size, and primary sales goals?"
    );
  }

  if (
    normalized.includes("hello") ||
    normalized.includes("hi") ||
    normalized.includes("hey") ||
    normalized.includes("namaste")
  ) {
    return (
      "Hello! Welcome to Autonomous AI Sales Agent. I can walk you through our product capabilities, discuss customized pricing, or help schedule a demo. What would you like to explore first?"
    );
  }

  return (
    "Thank you for sharing that. Could you tell me a little more about what you're looking to solve—for example, whether you're exploring our product features, pricing, or scheduling a demo?"
  );
}

export async function generateMockAgentReply({ message, history = [], language = "en-IN" }) {
  if (!message || !message.trim()) {
    throw new Error("Cannot generate a response for an empty message.");
  }

  // Simulate realistic response latency without calling an external API.
  await new Promise((resolve) => setTimeout(resolve, 450));

  const replyText = buildSalesReply(message);

  return {
    id: `assistant-${Date.now()}`,
    role: "assistant",
    content: replyText,
    timestamp: new Date().toISOString(),
    isMock: true,
    language,
    historyLength: history.length,
  };
}
