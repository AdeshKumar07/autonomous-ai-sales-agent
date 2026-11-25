import {
  Activity,
  AlertTriangle,
  HeartHandshake,
  Minus,
  Smile,
  Sparkles,
  ThumbsDown,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

const SENTIMENT_STYLES = {
  POSITIVE: {
    badge: "border-emerald-200 bg-emerald-50 text-emerald-700",
    bar: "bg-emerald-500",
    icon: Smile,
  },
  NEUTRAL: {
    badge: "border-slate-200 bg-slate-100 text-slate-700",
    bar: "bg-slate-400",
    icon: Minus,
  },
  FRUSTRATED: {
    badge: "border-amber-200 bg-amber-50 text-amber-800",
    bar: "bg-amber-500",
    icon: AlertTriangle,
  },
  NEGATIVE: {
    badge: "border-rose-200 bg-rose-50 text-rose-700",
    bar: "bg-rose-500",
    icon: ThumbsDown,
  },
};

const TREND_META = {
  improving: {
    label: "Improving",
    style: "text-emerald-700 bg-emerald-50 border-emerald-200",
    icon: TrendingUp,
  },
  stable: {
    label: "Stable",
    style: "text-slate-700 bg-slate-100 border-slate-200",
    icon: Minus,
  },
  declining: {
    label: "Declining",
    style: "text-rose-700 bg-rose-50 border-rose-200",
    icon: TrendingDown,
  },
  insufficient_data: {
    label: "Insufficient Data",
    style: "text-slate-500 bg-slate-50 border-slate-200",
    icon: Activity,
  },
};

function SentimentPanel({ sentimentSummary }) {
  const latestLabel = sentimentSummary?.latest_sentiment || null;
  const overallLabel = sentimentSummary?.overall_sentiment || null;
  const trendKey = sentimentSummary?.sentiment_trend || "insufficient_data";
  const confidence = sentimentSummary?.latest_confidence;
  const confidencePct =
    typeof confidence === "number" ? Math.round(confidence * 100) : null;

  const latestStyle = SENTIMENT_STYLES[latestLabel] || SENTIMENT_STYLES.NEUTRAL;
  const LatestIcon = latestStyle.icon;
  const overallStyle = SENTIMENT_STYLES[overallLabel] || SENTIMENT_STYLES.NEUTRAL;
  const trendInfo = TREND_META[trendKey] || TREND_META.insufficient_data;
  const TrendIcon = trendInfo.icon;

  const indicators = sentimentSummary?.latest_emotional_indicators || [];

  return (
    <div className="p-4 lg:p-5 space-y-4">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-indigo-600" />
          <h2 className="text-sm font-semibold text-slate-900">Sentiment Analysis</h2>
        </div>
        {latestLabel ? (
          <span
            className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${latestStyle.badge}`}
          >
            <LatestIcon className="h-3.5 w-3.5" />
            <span>{latestLabel}</span>
          </span>
        ) : (
          <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-2.5 py-0.5 text-xs font-medium text-slate-500">
            Waiting
          </span>
        )}
      </div>

      {!latestLabel ? (
        <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50/70 p-4 text-center text-xs text-slate-500">
          Send a customer message to view real-time sentiment classification,
          confidence, emotional cues, and conversation trend.
        </p>
      ) : (
        <>
          {/* Confidence */}
          <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-3">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-slate-600">Confidence Score</span>
              <span className="font-semibold text-slate-900">
                {confidencePct !== null ? `${confidencePct}% (${confidence})` : "N/A"}
              </span>
            </div>
            {confidencePct !== null && (
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-200">
                <div
                  className={`h-full rounded-full transition-all ${latestStyle.bar}`}
                  style={{ width: `${confidencePct}%` }}
                />
              </div>
            )}
          </div>

          {/* Overall & Trend */}
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
              <p className="text-[11px] uppercase tracking-wide text-slate-400">Overall</p>
              <span
                className={`mt-1 inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-semibold ${overallStyle.badge}`}
              >
                {overallLabel || "N/A"}
              </span>
            </div>
            <div className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
              <p className="text-[11px] uppercase tracking-wide text-slate-400">Trend</p>
              <span
                className={`mt-1 inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold ${trendInfo.style}`}
              >
                <TrendIcon className="h-3 w-3" />
                <span>{trendInfo.label}</span>
              </span>
            </div>
          </div>

          {/* Explanation */}
          {sentimentSummary?.latest_explanation && (
            <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-3">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                Explanation
              </p>
              <p className="mt-1 text-xs leading-relaxed text-slate-700">
                {sentimentSummary.latest_explanation}
              </p>
            </div>
          )}

          {/* Emotional Indicators */}
          <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-3">
            <p className="flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              <Sparkles className="h-3 w-3" />
              <span>Emotional Indicators</span>
            </p>
            {indicators.length > 0 ? (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {indicators.map((cue) => (
                  <span
                    key={cue}
                    className="rounded-md border border-slate-200 bg-white px-2 py-0.5 text-[11px] font-medium text-slate-700"
                  >
                    {cue}
                  </span>
                ))}
              </div>
            ) : (
              <p className="mt-1 text-xs text-slate-400">No strong emotional cues detected.</p>
            )}
          </div>

          {/* Recommended Strategy */}
          {sentimentSummary?.latest_recommended_strategy && (
            <div className="rounded-xl border border-indigo-100 bg-indigo-50/60 p-3">
              <p className="flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wide text-indigo-700">
                <HeartHandshake className="h-3.5 w-3.5" />
                <span>Recommended Strategy</span>
              </p>
              <p className="mt-1 text-xs leading-relaxed text-indigo-900">
                {sentimentSummary.latest_recommended_strategy}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default SentimentPanel;
