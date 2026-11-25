import { CalendarDays } from "lucide-react";

function AppointmentCalendar({ appointments }) {
  const upcoming = appointments.filter((a) => a.status !== "CANCELLED");

  const grouped = upcoming.reduce((acc, appt) => {
    const dayKey = new Date(appt.scheduled_start).toLocaleDateString([], {
      timeZone: appt.timezone || "UTC",
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric",
    });
    if (!acc[dayKey]) acc[dayKey] = [];
    acc[dayKey].push(appt);
    return acc;
  }, {});

  const entries = Object.entries(grouped);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4">
      <div className="flex items-center gap-2">
        <CalendarDays className="h-4 w-4 text-indigo-600" />
        <h3 className="text-sm font-semibold text-slate-900">Upcoming Schedule</h3>
      </div>

      {entries.length === 0 ? (
        <p className="text-xs text-slate-400">No upcoming active appointments scheduled.</p>
      ) : (
        <div className="space-y-3">
          {entries.map(([day, items]) => (
            <div key={day} className="space-y-1.5">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                {day}
              </p>
              <div className="space-y-1.5">
                {items.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-xs"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-medium text-slate-800">
                        {item.customer_name || "Customer"} — {item.appointment_type}
                      </p>
                      <p className="text-[11px] text-slate-500">
                        {item.appointment_reference}
                      </p>
                    </div>
                    <span className="shrink-0 font-semibold text-indigo-700">
                      {new Date(item.scheduled_start).toLocaleTimeString([], {
                        timeZone: item.timezone || "UTC",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default AppointmentCalendar;
