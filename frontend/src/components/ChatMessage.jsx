import { Bot, User, Volume2 } from "lucide-react";

function formatTimestamp(isoString) {
  if (!isoString) return "";
  try {
    return new Date(isoString).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

function ChatMessage({ message, onReplaySpeech, isMuted }) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex items-start gap-3 ${
        isUser ? "flex-row-reverse" : "flex-row"
      }`}
    >
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${
          isUser
            ? "border-indigo-600 bg-indigo-600 text-white"
            : "border-slate-200 bg-white text-indigo-600 shadow-xs"
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div
        className={`flex max-w-[82%] flex-col gap-1 sm:max-w-[72%] ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        <div
          className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-xs ${
            isUser
              ? "rounded-tr-sm bg-indigo-600 text-white"
              : "rounded-tl-sm border border-slate-200 bg-white text-slate-800"
          }`}
        >
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
          {!isUser && Array.isArray(message.sources) && message.sources.length > 0 && (
            <div className="mt-2 flex flex-wrap items-center gap-1 border-t border-slate-100 pt-2">
              <span className="text-[10px] font-medium text-slate-400">Sources:</span>
              {message.sources.map((src) => (
                <span
                  key={src}
                  className="rounded-md bg-indigo-50 px-1.5 py-0.5 text-[10px] font-medium text-indigo-700"
                >
                  {src}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 px-1 text-[11px] text-slate-400">
          <span>{isUser ? "You" : "AI Sales Assistant"}</span>
          <span>•</span>
          <span>{formatTimestamp(message.timestamp)}</span>
          {!isUser && onReplaySpeech && !isMuted && (
            <button
              type="button"
              onClick={() => onReplaySpeech(message.content)}
              title="Replay voice response"
              className="inline-flex items-center gap-1 rounded px-1 py-0.5 text-slate-500 transition-colors hover:bg-slate-100 hover:text-indigo-600"
            >
              <Volume2 className="h-3 w-3" />
              <span>Speak</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default ChatMessage;
