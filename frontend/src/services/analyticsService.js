import api from "./api";

export async function fetchAnalyticsBundle(params = {}) {
  const [overview, leads, sentiment, appointments, insights] = await Promise.all([
    api.get("/api/analytics/overview", { params }).then((r) => r.data),
    api.get("/api/analytics/leads", { params }).then((r) => r.data),
    api.get("/api/analytics/sentiment", { params }).then((r) => r.data),
    api.get("/api/analytics/appointments", { params }).then((r) => r.data),
    api.get("/api/analytics/sales-insights", { params }).then((r) => r.data),
  ]);

  return { overview, leads, sentiment, appointments, insights };
}
