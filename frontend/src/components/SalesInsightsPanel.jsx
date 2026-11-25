import { AlertCircle, HelpCircle, Lightbulb, MessageSquareWarning, Target } from "lucide-react";

function InsightList({ icon: Icon, title, items, emptyText }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs space-y-2.5">
      <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
        <Icon className="h-3.5 w-3.5 text-indigo-600" />
        <span>{title}</span>
      </h4>
      {items && items.length > 0 ? (
        <ul className="space-y-1.5">
          {items.map((item) => (
            <li
              key={item.label}
              className="flex items-center justify-between gap-2 rounded-lg bg-slate-50 px-3 py-1.5 text-xs"
            >
              <span className="text-slate-800">{item.label}</span>
              <span className="shrink-0 rounded bg-white px-2 py-0.5 text-[10px] font-semibold text-slate-500 border border-slate-200">
                {item.count}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-xs text-slate-400">{emptyText}</p>
      )}
    </div>
  );
}

function SalesInsightsPanel({ insights }) {
  if (!insights) return null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <InsightList
          icon={Target}
          title="Top Customer Requirements"
          items={insights.top_requirements}
          emptyText="No requirements recorded in this period."
        />
        <InsightList
          icon={AlertCircle}
          title="Common Pain Points"
          items={insights.common_pain_points}
          emptyText="No pain points recorded in this period."
        />
        <InsightList
          icon={MessageSquareWarning}
          title="Frequently Raised Objections"
          items={insights.common_objections}
          emptyText="No objections recorded in this period."
        />
        <InsightList
          icon={HelpCircle}
          title="Common Customer Questions"
          items={insights.frequently_asked_questions}
          emptyText="No customer questions recorded in this period."
        />
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-3">
        <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
          <Lightbulb className="h-4 w-4 text-amber-500" />
          <span>Suggested Sales Follow-Up Actions</span>
        </h4>
        {insights.recommended_follow_ups?.length > 0 ? (
          <div className="space-y-2">
            {insights.recommended_follow_ups.map((rec) => (
              <div
                key={rec.lead_id}
                className="flex flex-col justify-between gap-2 rounded-xl border border-slate-100 bg-slate-50/70 p-3 text-xs sm:flex-row sm:items-center"
              >
                <div className="min-w-0">
                  <p className="font-semibold text-slate-800">
                    {rec.customer_name || rec.session_id} ({rec.qualification_status}
                    {rec.latest_sentiment ? ` • ${rec.latest_sentiment}` : ""})
                  </p>
                  <p className="mt-0.5 text-slate-600">{rec.recommended_action}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-400">No follow-up actions available yet.</p>
        )}
      </div>
    </div>
  );
}

export default SalesInsightsPanel;
