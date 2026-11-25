import { AlertCircle, Bot, Sparkles, X } from "lucide-react";
import { useEffect, useRef } from "react";
import ChatMessage from "./ChatMessage";

const SAMPLE_PROMPTS = [
  "Tell me about your product features",
  "What is your pricing?",
  "I'd like to schedule a demo",
  "I'm interested in getting started",
];

function ChatWindow({
  messages,
  isThinking,
  error,
  onDismissError,
  onSelectPrompt,
  onReplaySpeech,
  isMuted,
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-5 sm:px-6">
      <div className="mx-auto flex max-w-4xl flex-col gap-4">
        {error && (
          <div
            role="alert"
            className="flex items-start justify-between gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
          >
            <div className="flex items-start gap-2.5">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" />
              <span>{error}</span>
            </div>
            <button
              type="button"
              onClick={onDismissError}
              aria-label="Dismiss error"
              className="rounded p-0.5 text-rose-500 hover:bg-rose-100 hover:text-rose-700"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {messages.length === 0 ? (
          <div className="my-6 flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-10 text-center shadow-xs">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
              <Bot className="h-6 w-6" />
            </div>
            <h2 className="mt-4 text-lg font-semibold text-slate-900">
              Welcome to Autonomous AI Sales Agent
            </h2>
            <p className="mt-2 max-w-md text-sm text-slate-600">
              Click the microphone button below to start a live voice
              conversation, or type a message. Ask about products, pricing, or
              scheduling a demo.
            </p>
            <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
              {SAMPLE_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => onSelectPrompt(prompt)}
                  className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3.5 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700"
                >
                  <Sparkles className="h-3 w-3 text-indigo-500" />
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              message={msg}
              onReplaySpeech={onReplaySpeech}
              isMuted={isMuted}
            />
          ))
        )}

        {isThinking && (
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-white text-indigo-600 shadow-xs">
              <Bot className="h-4 w-4" />
            </div>
            <div className="rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-4 py-3 shadow-xs">
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:-0.3s]" />
                <span className="h-2 w-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:-0.15s]" />
                <span className="h-2 w-2 rounded-full bg-indigo-400 animate-bounce" />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}

export default ChatWindow;
