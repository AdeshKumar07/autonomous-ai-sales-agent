import { Calendar, Clock, Globe, RefreshCw, Video, XCircle } from "lucide-react";
import { useState } from "react";
import { cancelAppointment, rescheduleAppointment } from "../services/appointmentService";

const STATUS_BADGE = {
  CONFIRMED: "border-emerald-200 bg-emerald-50 text-emerald-700",
  PENDING: "border-amber-200 bg-amber-50 text-amber-700",
  CANCELLED: "border-rose-200 bg-rose-50 text-rose-700",
  COMPLETED: "border-indigo-200 bg-indigo-50 text-indigo-700",
  NO_SHOW: "border-slate-200 bg-slate-100 text-slate-700",
};

function formatInTimezone(isoString, tz) {
  try {
    return new Date(isoString).toLocaleString([], {
      timeZone: tz || "UTC",
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return isoString;
  }
}

function AppointmentPanel({ appointments, sessionId, onUpdated }) {
  const [busyId, setBusyId] = useState(null);
  const [rescheduleId, setRescheduleId] = useState(null);
  const [newStart, setNewStart] = useState("");
  const [error, setError] = useState("");

  const handleCancel = async (id) => {
    setBusyId(id);
    setError("");
    try {
      await cancelAppointment(id, { reason: "Cancelled from dashboard", sessionId });
      onUpdated?.();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to cancel appointment.");
    } finally {
      setBusyId(null);
    }
  };

  const handleRescheduleSubmit = async (e, appt) => {
    e.preventDefault();
    if (!newStart) return;
    setBusyId(appt.id);
    setError("");
    try {
      const startDt = new Date(newStart);
      const endDt = new Date(startDt.getTime() + 30 * 60000);
      await rescheduleAppointment(appt.id, {
        scheduled_start: startDt.toISOString(),
        scheduled_end: endDt.toISOString(),
        timezone: appt.timezone,
        session_id: sessionId,
      });
      setRescheduleId(null);
      setNewStart("");
      onUpdated?.();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to reschedule appointment.");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">Appointments</h3>
        <span className="text-xs text-slate-500">{appointments.length} total</span>
      </div>

      {error && (
        <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {error}
        </p>
      )}

      {appointments.length === 0 ? (
        <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4 text-center text-xs text-slate-500">
          No appointments booked yet.
        </p>
      ) : (
        <div className="space-y-3">
          {appointments.map((appt) => (
            <div
              key={appt.id}
              className="rounded-xl border border-slate-200 bg-slate-50/60 p-3.5 space-y-2"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs font-bold text-indigo-700">
                  {appt.appointment_reference}
                </span>
                <span
                  className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${
                    STATUS_BADGE[appt.status] || STATUS_BADGE.PENDING
                  }`}
                >
                  {appt.status}
                </span>
              </div>

              <div className="text-xs font-medium text-slate-800">
                {appt.title} ({appt.appointment_type})
              </div>

              <div className="grid grid-cols-1 gap-1 text-[11px] text-slate-600 sm:grid-cols-2">
                <span className="flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5 text-slate-400" />
                  {formatInTimezone(appt.scheduled_start, appt.timezone)}
                </span>
                <span className="flex items-center gap-1.5">
                  <Globe className="h-3.5 w-3.5 text-slate-400" />
                  {appt.timezone}
                </span>
                {appt.customer_name && (
                  <span className="flex items-center gap-1.5">
                    <Clock className="h-3.5 w-3.5 text-slate-400" />
                    {appt.customer_name}
                  </span>
                )}
                {appt.meeting_link && (
                  <span className="flex items-center gap-1.5 truncate text-indigo-600">
                    <Video className="h-3.5 w-3.5 shrink-0" />
                    <span className="truncate">{appt.meeting_link}</span>
                  </span>
                )}
              </div>

              {appt.status !== "CANCELLED" && (
                <div className="flex flex-wrap gap-2 pt-1">
                  <button
                    type="button"
                    disabled={busyId === appt.id}
                    onClick={() =>
                      setRescheduleId(rescheduleId === appt.id ? null : appt.id)
                    }
                    className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-700 hover:bg-slate-100"
                  >
                    <RefreshCw className="h-3 w-3" />
                    Reschedule
                  </button>
                  <button
                    type="button"
                    disabled={busyId === appt.id}
                    onClick={() => handleCancel(appt.id)}
                    className="inline-flex items-center gap-1 rounded-lg border border-rose-200 bg-rose-50 px-2.5 py-1 text-[11px] font-medium text-rose-700 hover:bg-rose-100"
                  >
                    <XCircle className="h-3 w-3" />
                    Cancel
                  </button>
                </div>
              )}

              {rescheduleId === appt.id && (
                <form
                  onSubmit={(e) => handleRescheduleSubmit(e, appt)}
                  className="mt-2 flex flex-wrap items-center gap-2 border-t border-slate-200 pt-2"
                >
                  <input
                    type="datetime-local"
                    value={newStart}
                    onChange={(e) => setNewStart(e.target.value)}
                    required
                    className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-xs"
                  />
                  <button
                    type="submit"
                    disabled={busyId === appt.id}
                    className="rounded-lg bg-indigo-600 px-3 py-1 text-xs font-medium text-white hover:bg-indigo-700"
                  >
                    Save
                  </button>
                </form>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default AppointmentPanel;
