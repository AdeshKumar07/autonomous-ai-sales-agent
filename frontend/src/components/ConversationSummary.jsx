import { CheckCircle2, FileText, RefreshCw, Sparkles } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { fetchSessionSummary, generateSessionSummary } from "../services/summaryService";

function ListSection({ title, items, emptyText }) {
  return (
    <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-3.5">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
        {title}
      </p>
      {items && items.length > 0 ? (
        <ul className="mt-1.5 list-disc pl-4 space-y-1 text-xs text-slate-700">
          {items.map((item, idx) => (
            <li key={`${title}-${idx}`}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-1 text-xs text-slate-400">{emptyText || "Not provided"}</p>
      )}
    </div>
  );
}

function ConversationSummary({ sessionId }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  const loadSummary = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    setError("");
    try {
      const data = await fetchSessionSummary(sessionId);
      setSummary(data);
    } catch {
      setError("Failed to load conversation summary.");
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    let active = true;
    if (!sessionId) return;
    fetchSessionSummary(sessionId)
      .then((data) => {
        if (active) setSummary(data);
      })
      .catch(() => {
        if (active) setError("Failed to load conversation summary.");
      });
    return () => {
      active = false;
    };
  }, [sessionId]);

  const handleGenerate = async (isCompleted = false) => {
    setGenerating(true);
    setError("");
    try {
      const data = await generateSessionSummary(sessionId, isCompleted);
      setSummary(data);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to generate summary. Ensure at least one message exists."
      );
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl p-4 sm:p-6 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
        <div>
          <h2 className="flex items-center gap-2 text-base font-semibold text-slate-900">
            <FileText className="h-4 w-4 text-indigo-600" />
            <span>Call & Conversation Summary</span>
          </h2>
          <p className="mt-0.5 text-xs text-slate-500">
            Session: <span className="font-mono">{sessionId}</span>
            {summary?.generated_at && (
              <> • Last generated: {new Date(summary.generated_at).toLocaleString()}</>
            )}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => handleGenerate(false)}
            disabled={generating}
            className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${generating ? "animate-spin" : ""}`} />
            <span>
              {generating
                ? "Generating..."
                : summary
                  ? "Regenerate Summary"
                  : "Generate Summary"}
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleGenerate(true)}
            disabled={generating}
            className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-200 bg-emerald-50 px-3.5 py-2 text-xs font-semibold text-emerald-700 hover:bg-emerald-100 disabled:opacity-50"
          >
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Mark Completed</span>
          </button>

          <button
            type="button"
            onClick={loadSummary}
            disabled={loading}
            className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100"
          >
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-xs text-rose-700">
          {error}
        </p>
      )}

      {!summary ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-xs text-slate-500">
          No summary has been generated for this session yet. Click{" "}
          <strong>Generate Summary</strong> after conversing with the AI sales agent.
        </div>
      ) : (
        <div className="space-y-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-base font-semibold text-slate-900">
                {summary.conversation_title}
              </h3>
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full border border-slate-200 bg-slate-100 px-2.5 py-0.5 text-[11px] font-semibold text-slate-700">
                  {summary.is_conversation_completed ? "Completed" : "In Progress"}
                </span>
                <span className="rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-0.5 text-[11px] font-semibold text-indigo-700">
                  {summary.qualification_status}
                </span>
                <span className="text-[11px] text-slate-400">v{summary.summary_version}</span>
              </div>
            </div>

            <p className="text-sm leading-relaxed text-slate-700">{summary.summary}</p>

            <div className="grid grid-cols-1 gap-2 pt-2 text-xs sm:grid-cols-4">
              <div className="rounded-lg bg-slate-50 p-2.5">
                <span className="text-slate-400 block">Customer</span>
                <span className="font-medium text-slate-800">
                  {summary.customer_name || "Not provided"}
                </span>
              </div>
              <div className="rounded-lg bg-slate-50 p-2.5">
                <span className="text-slate-400 block">Company</span>
                <span className="font-medium text-slate-800">
                  {summary.company_name || "Not provided"}
                </span>
              </div>
              <div className="rounded-lg bg-slate-50 p-2.5">
                <span className="text-slate-400 block">Budget & Timeline</span>
                <span className="font-medium text-slate-800">
                  {summary.budget || "Not provided"} • {summary.purchase_timeline || "Not provided"}
                </span>
              </div>
              <div className="rounded-lg bg-slate-50 p-2.5">
                <span className="text-slate-400 block">Appointment</span>
                <span className="font-medium text-slate-800">
                  {summary.appointment_reference || "None"}
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <ListSection title="Customer Requirements" items={summary.customer_requirements} />
            <ListSection title="Pain Points" items={summary.pain_points} />
            <ListSection title="Discussed Products" items={summary.discussed_products} />
            <ListSection title="Objections" items={summary.objections} />
            <ListSection title="Customer Questions" items={summary.customer_questions} />
            <ListSection title="Unresolved Questions" items={summary.unresolved_questions} />
          </div>

          <div className="rounded-2xl border border-indigo-200 bg-indigo-50/70 p-4 space-y-1">
            <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-indigo-700">
              <Sparkles className="h-3.5 w-3.5" />
              Recommended Next Sales Action
            </p>
            <p className="text-sm font-medium text-indigo-950">
              {summary.recommended_next_action}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default ConversationSummary;
