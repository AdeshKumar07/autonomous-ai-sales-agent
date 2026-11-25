import { Bot, Globe, Volume2, VolumeX } from "lucide-react";
import { SUPPORTED_LANGUAGES } from "../services/voiceService";
import ConnectionStatus from "./ConnectionStatus";

function Header({
  language,
  onLanguageChange,
  isMuted,
  onToggleMute,
  activeView,
  onViewChange,
}) {
  const navItems = [
    { id: "voice", label: "Voice Agent" },
    { id: "appointments", label: "Appointments" },
    { id: "crm", label: "CRM" },
  ];

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-sm">
            <Bot className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-base font-semibold text-slate-900 sm:text-lg">
              Autonomous AI Sales Agent
            </h1>
            <p className="truncate text-xs text-slate-500">
              FORTIVEX AI — Gemini Voice, RAG & CRM
            </p>
          </div>
        </div>

        <nav className="flex items-center gap-1 rounded-xl border border-slate-200 bg-slate-100 p-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => onViewChange(item.id)}
              className={`rounded-lg px-3 py-1 text-xs font-semibold transition-colors ${
                activeView === item.id
                  ? "bg-white text-indigo-700 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          <ConnectionStatus />

          <div className="relative flex items-center">
            <Globe className="pointer-events-none absolute left-2.5 h-3.5 w-3.5 text-slate-500" />
            <select
              aria-label="Select speech language"
              value={language}
              onChange={(e) => onLanguageChange(e.target.value)}
              className="rounded-lg border border-slate-200 bg-slate-50 py-1.5 pl-8 pr-2.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-100 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              {SUPPORTED_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.label}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            onClick={onToggleMute}
            aria-label={isMuted ? "Unmute voice responses" : "Mute voice responses"}
            title={isMuted ? "Unmute AI voice" : "Mute AI voice"}
            className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors ${
              isMuted
                ? "border-slate-200 bg-slate-100 text-slate-600 hover:bg-slate-200"
                : "border-indigo-200 bg-indigo-50 text-indigo-700 hover:bg-indigo-100"
            }`}
          >
            {isMuted ? (
              <VolumeX className="h-4 w-4" />
            ) : (
              <Volume2 className="h-4 w-4" />
            )}
            <span className="hidden sm:inline">
              {isMuted ? "Muted" : "Voice On"}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}

export default Header;
