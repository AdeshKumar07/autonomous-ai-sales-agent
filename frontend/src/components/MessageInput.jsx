import { Mic, MicOff, Send } from "lucide-react";
import { useState } from "react";

function MessageInput({
  onSendMessage,
  isThinking,
  isListening,
  isSpeechSupported,
  onToggleListening,
}) {
  const [text, setText] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || isThinking) return;
    onSendMessage(trimmed);
    setText("");
  };

  return (
    <footer className="border-t border-slate-200 bg-white px-4 py-3 sm:px-6">
      <form
        onSubmit={handleSubmit}
        className="mx-auto flex max-w-4xl items-center gap-2"
      >
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type a message or use the microphone..."
          aria-label="Type your message"
          className="flex-1 rounded-xl border border-slate-300 bg-slate-50 px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
        />

        <button
          type="button"
          onClick={onToggleListening}
          disabled={!isSpeechSupported}
          aria-label={isListening ? "Stop microphone" : "Start microphone"}
          title={
            isSpeechSupported
              ? isListening
                ? "Stop microphone"
                : "Start microphone"
              : "Speech recognition not supported"
          }
          className={`inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${
            isListening
              ? "border-rose-300 bg-rose-50 text-rose-600 hover:bg-rose-100"
              : "border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100 hover:text-indigo-600"
          }`}
        >
          {isListening ? (
            <MicOff className="h-4 w-4" />
          ) : (
            <Mic className="h-4 w-4" />
          )}
        </button>

        <button
          type="submit"
          disabled={!text.trim() || isThinking}
          aria-label="Send message"
          className="inline-flex h-10 items-center gap-1.5 rounded-xl bg-indigo-600 px-4 text-sm font-medium text-white shadow-xs transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Send className="h-4 w-4" />
          <span className="hidden sm:inline">Send</span>
        </button>
      </form>
    </footer>
  );
}

export default MessageInput;
