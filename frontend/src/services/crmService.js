import api from "./api";

export async function fetchCrmLeads() {
  const response = await api.get("/api/crm/leads");
  return response.data;
}

export async function fetchCrmLeadDetail(leadId) {
  const response = await api.get(`/api/crm/leads/${leadId}`);
  return response.data;
}

export async function addCrmLeadNote(leadId, { note, nextFollowUp }) {
  const response = await api.post(`/api/crm/leads/${leadId}/notes`, {
    note,
    next_follow_up: nextFollowUp || undefined,
  });
  return response.data;
}
