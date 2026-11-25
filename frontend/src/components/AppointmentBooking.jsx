import { CalendarCheck, CheckCircle2, Clock } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { createAppointment, fetchAvailability } from "../services/appointmentService";

const TIMEZONES = ["UTC", "Asia/Kolkata", "America/New_York", "Europe/London"];

function nextWeekdayIso() {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  while (d.getDay() === 0 || d.getDay() === 6) {
    d.setDate(d.getDate() + 1);
  }
  return d.toISOString().slice(0, 10);
}

function AppointmentBooking({ sessionId, lead, onBooked }) {
  const [date, setDate] = useState(nextWeekdayIso);
  const [appointmentType, setAppointmentType] = useState("DEMO");
  const [timezone, setTimezone] = useState("UTC");
  const [availability, setAvailability] = useState(null);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(null);

  const [customerName, setCustomerName] = useState(lead?.customer_name || "");
  const [customerEmail, setCustomerEmail] = useState(lead?.email || "");
  const [customerPhone, setCustomerPhone] = useState(lead?.phone || "");
  const [submitting, setSubmitting] = useState(false);
  const [confirmation, setConfirmation] = useState(null);
  const [error, setError] = useState("");

  const loadSlots = useCallback(async () => {
    setLoadingSlots(true);
    setError("");
    setSelectedSlot(null);
    try {
      const data = await fetchAvailability({ date, appointmentType, timezone });
      setAvailability(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load available slots.");
    } finally {
      setLoadingSlots(false);
    }
  }, [date, appointmentType, timezone]);

  useEffect(() => {
    let active = true;
    fetchAvailability({ date, appointmentType, timezone })
      .then((data) => {
        if (!active) return;
        setAvailability(data);
        setSelectedSlot(null);
        setError("");
      })
      .catch((err) => {
        if (active) setError(err.response?.data?.detail || "Failed to load available slots.");
      });
    return () => {
      active = false;
    };
  }, [date, appointmentType, timezone]);

  const handleConfirmBooking = async (e) => {
    e.preventDefault();
    if (!selectedSlot) return;
    setSubmitting(true);
    setError("");
    setConfirmation(null);

    try {
      const res = await createAppointment({
        lead_id: lead?.id || undefined,
        session_id: sessionId,
        title: `Fortivex AI ${appointmentType.replace("_", " ")}`,
        appointment_type: appointmentType,
        scheduled_start: selectedSlot.start_utc,
        scheduled_end: selectedSlot.end_utc,
        timezone,
        customer_name: customerName.trim() || undefined,
        customer_email: customerEmail.trim() || undefined,
        customer_phone: customerPhone.trim() || undefined,
      });
      setConfirmation(res);
      setSelectedSlot(null);
      await loadSlots();
      onBooked?.(res.appointment);
    } catch (err) {
      setError(err.response?.data?.detail || "Booking failed. Please choose another slot.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4">
      <div className="flex items-center gap-2">
        <CalendarCheck className="h-4 w-4 text-indigo-600" />
        <h3 className="text-sm font-semibold text-slate-900">Book Appointment</h3>
      </div>

      {error && (
        <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {error}
        </p>
      )}

      {confirmation && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800 space-y-1">
          <div className="flex items-center gap-1.5 font-semibold">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            <span>Confirmed: {confirmation.appointment_reference}</span>
          </div>
          <p>{confirmation.confirmation_message}</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div>
          <label className="block text-[11px] font-medium text-slate-500">Date</label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs"
          />
        </div>
        <div>
          <label className="block text-[11px] font-medium text-slate-500">Type</label>
          <select
            value={appointmentType}
            onChange={(e) => setAppointmentType(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs"
          >
            <option value="DEMO">Demo</option>
            <option value="ONLINE_MEETING">Online Meeting</option>
            <option value="CALL">Call</option>
          </select>
        </div>
        <div>
          <label className="block text-[11px] font-medium text-slate-500">Timezone</label>
          <select
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs"
          >
            {TIMEZONES.map((tz) => (
              <option key={tz} value={tz}>
                {tz}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <p className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
          <Clock className="h-3.5 w-3.5" />
          <span>Available Slots ({timezone})</span>
        </p>
        {loadingSlots ? (
          <p className="text-xs text-slate-400">Checking backend availability...</p>
        ) : !availability?.is_working_day ? (
          <p className="text-xs text-amber-700">Selected date is outside working days (Mon–Fri).</p>
        ) : availability?.available_slots?.length === 0 ? (
          <p className="text-xs text-slate-500">No available slots for this date.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {availability?.available_slots?.map((slot) => {
              const isSelected = selectedSlot?.start_utc === slot.start_utc;
              return (
                <button
                  key={slot.start_utc}
                  type="button"
                  onClick={() => setSelectedSlot(slot)}
                  className={`rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors ${
                    isSelected
                      ? "border-indigo-600 bg-indigo-600 text-white"
                      : "border-slate-200 bg-slate-50 text-slate-700 hover:border-indigo-300 hover:bg-indigo-50"
                  }`}
                >
                  {slot.display_start}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {selectedSlot && (
        <form onSubmit={handleConfirmBooking} className="space-y-3 border-t border-slate-200 pt-3">
          <p className="text-xs font-semibold text-slate-700">
            Confirm Details for {selectedSlot.display_start} – {selectedSlot.display_end} ({timezone})
          </p>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            <input
              type="text"
              placeholder="Customer Name"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              required
              className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs"
            />
            <input
              type="email"
              placeholder="Email (optional)"
              value={customerEmail}
              onChange={(e) => setCustomerEmail(e.target.value)}
              className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs"
            />
            <input
              type="tel"
              placeholder="Phone (optional)"
              value={customerPhone}
              onChange={(e) => setCustomerPhone(e.target.value)}
              className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs"
            />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {submitting ? "Booking..." : "Confirm Appointment"}
          </button>
        </form>
      )}
    </div>
  );
}

export default AppointmentBooking;
