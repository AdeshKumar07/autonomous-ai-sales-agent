import api from "./api";

export async function fetchAvailability({ date, appointmentType = "DEMO", timezone = "UTC" }) {
  const response = await api.get("/api/appointments/availability", {
    params: {
      date,
      appointment_type: appointmentType,
      timezone,
    },
  });
  return response.data;
}

export async function createAppointment(payload) {
  const response = await api.post("/api/appointments", payload);
  return response.data;
}

export async function fetchAppointments(filters = {}) {
  const response = await api.get("/api/appointments", { params: filters });
  return response.data;
}

export async function cancelAppointment(appointmentId, { reason, sessionId } = {}) {
  const response = await api.patch(`/api/appointments/${appointmentId}/cancel`, {
    reason: reason || undefined,
    session_id: sessionId || undefined,
  });
  return response.data;
}

export async function rescheduleAppointment(appointmentId, payload) {
  const response = await api.patch(`/api/appointments/${appointmentId}/reschedule`, payload);
  return response.data;
}
