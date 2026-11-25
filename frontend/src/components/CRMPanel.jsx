import { Briefcase, Clock, FileText, Plus, Users } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { addCrmLeadNote, fetchCrmLeadDetail, fetchCrmLeads } from "../services/crmService";

function CRMPanel() {
  const [leads, setLeads] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [note, setNote] = useState("");
  const [nextFollowUp, setNextFollowUp] = useState("");
  const [savingNote, setSavingNote] = useState(false);
  const [error, setError] = useState("");

  const loadLeads = useCallback(async () => {
    setError("");
    try {
      const data = await fetchCrmLeads();
      setLeads(data);
      if (data.length > 0 && !selectedId) {
        setSelectedId(data[0].id);
      }
    } catch {
      setError("Failed to load CRM leads.");
    }
  }, [selectedId]);

  useEffect(() => {
    let active = true;
    fetchCrmLeads()
      .then((data) => {
        if (!active) return;
        setLeads(data);
        if (data.length > 0) {
          setSelectedId((prev) => prev || data[0].id);
        }
      })
      .catch(() => {
        if (active) setError("Failed to load CRM leads.");
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    let active = true;
    fetchCrmLeadDetail(selectedId)
      .then((data) => {
        if (active) setDetail(data);
      })
      .catch(() => {
        if (active) setError("Failed to load lead details.");
      });
    return () => {
      active = false;
    };
  }, [selectedId]);

  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!selectedId || !note.trim()) return;
    setSavingNote(true);
    setError("");
    try {
      const updated = await addCrmLeadNote(selectedId, {
        note: note.trim(),
        nextFollowUp: nextFollowUp.trim() || undefined,
      });
      setDetail(updated);
      setNote("");
      setNextFollowUp("");
      await loadLeads();
    } catch {
      setError("Unable to save sales note.");
    } finally {
      setSavingNote(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl p-4 sm:p-6 space-y-4">
      {error && (
        <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Leads List */}
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
              <Users className="h-4 w-4 text-indigo-600" />
              <span>CRM Leads ({leads.length})</span>
            </h2>
          </div>

          {leads.length === 0 ? (
            <p className="text-xs text-slate-400">No leads recorded yet.</p>
          ) : (
            <div className="space-y-2 max-h-[520px] overflow-y-auto">
              {leads.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setSelectedId(item.id)}
                  className={`w-full rounded-xl border p-3 text-left transition-colors ${
                    selectedId === item.id
                      ? "border-indigo-500 bg-indigo-50/50"
                      : "border-slate-200 bg-slate-50/50 hover:bg-slate-100"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-xs font-semibold text-slate-900">
                      {item.customer_name || item.session_id}
                    </span>
                    <span className="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-[10px] font-semibold text-slate-700">
                      {item.qualification_status}
                    </span>
                  </div>
                  <p className="mt-0.5 truncate text-[11px] text-slate-500">
                    {item.company_name || "No company"} • {item.appointment_count} appts
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Lead Detail + Timeline + Notes */}
        <div className="lg:col-span-2 space-y-4">
          {!detail ? (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 text-center text-xs text-slate-400">
              Select a lead to view CRM details, appointments, and activity timeline.
            </div>
          ) : (
            <>
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h3 className="text-base font-semibold text-slate-900">
                      {detail.customer_name || "Unnamed Lead"}
                    </h3>
                    <p className="text-xs text-slate-500">
                      {detail.company_name || "Company unknown"} • {detail.email || "No email"} •{" "}
                      {detail.phone || "No phone"}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-0.5 text-xs font-semibold text-indigo-700">
                      {detail.qualification_status}
                    </span>
                    {detail.latest_sentiment && (
                      <span className="rounded-full border border-slate-200 bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700">
                        {detail.latest_sentiment} ({detail.sentiment_trend})
                      </span>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-2 text-xs sm:grid-cols-2">
                  <div className="rounded-lg bg-slate-50 p-2.5">
                    <span className="font-medium text-slate-500">Requirements: </span>
                    <span className="text-slate-800">{detail.requirements || "N/A"}</span>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-2.5">
                    <span className="font-medium text-slate-500">Budget / Timeline: </span>
                    <span className="text-slate-800">
                      {detail.budget || "N/A"} • {detail.purchase_timeline || "N/A"}
                    </span>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-2.5">
                    <span className="font-medium text-slate-500">Next Follow-Up: </span>
                    <span className="text-slate-800">{detail.next_follow_up || "None set"}</span>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-2.5">
                    <span className="font-medium text-slate-500">Appointments: </span>
                    <span className="text-slate-800">{detail.appointments.length}</span>
                  </div>
                </div>
              </div>

              {/* Internal Notes */}
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-3">
                <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <FileText className="h-3.5 w-3.5" />
                  Internal Sales Notes
                </h4>
                {detail.internal_notes && (
                  <pre className="whitespace-pre-wrap rounded-xl bg-slate-50 p-3 text-xs text-slate-700 font-sans">
                    {detail.internal_notes}
                  </pre>
                )}
                <form onSubmit={handleAddNote} className="flex flex-col gap-2 sm:flex-row">
                  <input
                    type="text"
                    placeholder="Add internal sales note..."
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    required
                    className="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs"
                  />
                  <input
                    type="text"
                    placeholder="Next follow-up (optional)"
                    value={nextFollowUp}
                    onChange={(e) => setNextFollowUp(e.target.value)}
                    className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs"
                  />
                  <button
                    type="submit"
                    disabled={savingNote}
                    className="inline-flex items-center justify-center gap-1 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    Add Note
                  </button>
                </form>
              </div>

              {/* Activity Timeline */}
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-3">
                <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <Briefcase className="h-3.5 w-3.5" />
                  Activity Timeline
                </h4>
                {detail.activities.length === 0 ? (
                  <p className="text-xs text-slate-400">No activities recorded yet.</p>
                ) : (
                  <ul className="space-y-2 max-h-60 overflow-y-auto">
                    {detail.activities.map((act) => (
                      <li
                        key={act.id}
                        className="flex items-start justify-between gap-3 rounded-lg border border-slate-100 bg-slate-50/70 px-3 py-2 text-xs"
                      >
                        <div>
                          <span className="font-semibold text-indigo-700">
                            {act.activity_type}
                          </span>
                          <p className="text-slate-700">{act.description}</p>
                        </div>
                        <span className="flex shrink-0 items-center gap-1 text-[10px] text-slate-400">
                          <Clock className="h-3 w-3" />
                          {new Date(act.created_at).toLocaleString()}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default CRMPanel;
