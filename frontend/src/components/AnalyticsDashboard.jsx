import { BarChart3, CalendarCheck, Flame, TrendingUp, Users } from "lucide-react";
import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchAnalyticsBundle } from "../services/analyticsService";
import SalesInsightsPanel from "./SalesInsightsPanel";

const PRESETS = [
  { id: "today", label: "Today" },
  { id: "7d", label: "7 Days" },
  { id: "30d", label: "30 Days" },
  { id: "90d", label: "90 Days" },
  { id: "custom", label: "Custom" },
];

function KpiCard({ icon: Icon, label, value, sub }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500">{label}</span>
        <Icon className="h-4 w-4 text-indigo-600" />
      </div>
      <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
      {sub && <p className="mt-1 text-[11px] text-slate-400">{sub}</p>}
    </div>
  );
}

function AnalyticsDashboard() {
  const [preset, setPreset] = useState("30d");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (preset === "custom" && (!startDate || !endDate)) return;
    let active = true;
    const params =
      preset === "custom"
        ? { preset, start_date: startDate, end_date: endDate }
        : { preset };

    fetchAnalyticsBundle(params)
      .then((res) => {
        if (!active) return;
        setData(res);
        setError("");
      })
      .catch((err) => {
        if (active) setError(err.response?.data?.detail || "Failed to load analytics.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [preset, startDate, endDate]);

  const ov = data?.overview;

  return (
    <div className="mx-auto max-w-6xl p-4 sm:p-6 space-y-5">
      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-indigo-600" />
          <h2 className="text-sm font-semibold text-slate-900">Business Insights Dashboard</h2>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {PRESETS.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setPreset(p.id)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                preset === p.id
                  ? "bg-indigo-600 text-white"
                  : "border border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100"
              }`}
            >
              {p.label}
            </button>
          ))}
          {preset === "custom" && (
            <div className="flex items-center gap-1.5">
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="rounded-lg border border-slate-200 px-2 py-1 text-xs"
              />
              <span className="text-xs text-slate-400">to</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="rounded-lg border border-slate-200 px-2 py-1 text-xs"
              />
            </div>
          )}
        </div>
      </div>

      {error && (
        <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-xs text-rose-700">
          {error}
        </p>
      )}

      {loading && !data ? (
        <p className="text-xs text-slate-500">Loading analytics from PostgreSQL...</p>
      ) : ov ? (
        <>
          {/* Summary KPI Cards */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            <KpiCard icon={Users} label="Total Leads" value={ov.total_leads} />
            <KpiCard icon={Flame} label="HOT Leads" value={ov.hot_leads} />
            <KpiCard icon={CalendarCheck} label="Total Appointments" value={ov.total_appointments} />
            <KpiCard icon={CalendarCheck} label="Confirmed" value={ov.confirmed_appointments} />
            <KpiCard
              icon={TrendingUp}
              label="Booking Rate"
              value={`${ov.appointment_booking_rate}%`}
              sub="Booked leads / total leads"
            />
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Lead Qualification Distribution
              </h3>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.leads.distribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#4f46e5" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Leads Created Over Time
              </h3>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.leads.leads_over_time}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="count" stroke="#4f46e5" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Sentiment Distribution
              </h3>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.sentiment.distribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#0ea5e9" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Sentiment Trend Over Time
              </h3>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.sentiment.sentiment_trend_over_time}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Line type="monotone" dataKey="POSITIVE" stroke="#10b981" strokeWidth={2} />
                    <Line type="monotone" dataKey="NEUTRAL" stroke="#64748b" strokeWidth={2} />
                    <Line type="monotone" dataKey="FRUSTRATED" stroke="#f59e0b" strokeWidth={2} />
                    <Line type="monotone" dataKey="NEGATIVE" stroke="#ef4444" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs lg:col-span-2">
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Appointment Status Distribution
              </h3>
              <div className="h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.appointments.status_distribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#10b981" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <SalesInsightsPanel insights={data.insights} />
        </>
      ) : null}
    </div>
  );
}

export default AnalyticsDashboard;
