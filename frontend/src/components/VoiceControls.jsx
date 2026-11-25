import { Mic, MicOff, Square, Trash2, Volume2 } from "lucide-react";

function VoiceControls({
  isSupported,
  voiceState,
  conversationMode,
  onConversationModeChange,
  interimTranscript,
  hasMessages,
  onToggleListening,
  onStopSpeaking,
  onClearConversation,
}) {
  const isListening = voiceState === "listening";
  const isProcessing = voiceState === "processing";
  const isSpeaking = voiceState === "speaking";
  const isMicDisabled = !isSupported || isProcessing || isSpeaking;

  const statusText = isListening
    ? "Listening... speak clearly into your microphone"
    : isProcessing
      ? "Processing your message with Gemini..."
      : isSpeaking
        ? "Speaking AI response..."
        : voiceState === "error"
          ? "Ready (check error message above)"
          : "Idle — ready for voice or text input";

  return (
    <section className="border-t border-slate-200 bg-slate-50/80 px-4 py-3 sm:px-6">
      <div className="mx-auto flex max-w-4xl flex-col gap-3">
        {!isSupported && (
          <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-center text-xs text-amber-800">
            Browser Speech Recognition is unavailable in this browser. You can
            still interact using the text input below.
          </p>
        )}

        <div className="flex flex-col items-center justify-between gap-3 sm:flex-row">
          {/* Left: Voice state & live transcript preview */}
          <div className="flex w-full flex-1 items-center gap-3 min-w-0">
            <div
              className={`flex h-2.5 w-2.5 shrink-0 rounded-full ${
                isListening
                  ? "bg-rose-500 animate-ping"
                  : isProcessing
                    ? "bg-amber-500 animate-pulse"
                    : isSpeaking
                      ? "bg-indigo-500 animate-pulse"
                      : "bg-slate-300"
              }`}
            />
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-slate-700">{statusText}</p>
              {isListening && interimTranscript ? (
                <p className="truncate text-xs italic text-indigo-600">
                  &ldquo;{interimTranscript}&rdquo;
                </p>
              ) : (
                <p className="truncate text-[11px] text-slate-400">
                  {isListening
                    ? "Live transcript will appear here as you speak"
                    : isProcessing
                      ? "Microphone paused while generating reply"
                      : isSpeaking
                        ? "Microphone paused during voice playback"
                        : "Click Start Listening to speak"}
                </p>
              )}
            </div>
          </div>

          {/* Center/Right: Mode selector + Primary mic button + TTS stop + Clear */}
          <div className="flex flex-wrap items-center justify-center gap-2 shrink-0">
            <select
              aria-label="Conversation mode"
              value={conversationMode}
              onChange={(e) => onConversationModeChange(e.target.value)}
              className="rounded-xl border border-slate-200 bg-white px-2.5 py-2 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-100 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="push-to-talk">Push-to-talk</option>
              <option value="continuous">Continuous</option>
            </select>

            {isSpeaking && (
              <button
                type="button"
                onClick={onStopSpeaking}
                className="inline-flex items-center gap-1.5 rounded-xl border border-amber-300 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800 transition-colors hover:bg-amber-100"
              >
                <Square className="h-3.5 w-3.5 fill-current" />
                <span>Stop Speaking</span>
              </button>
            )}

            <button
              type="button"
              onClick={onToggleListening}
              disabled={isMicDisabled}
              aria-label={isListening ? "Stop listening" : "Start listening"}
              className={`relative inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold shadow-sm transition-all focus:outline-none focus:ring-4 disabled:cursor-not-allowed disabled:opacity-50 ${
                isListening
                  ? "bg-rose-600 text-white hover:bg-rose-700 focus:ring-rose-500/30"
                  : "bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-indigo-500/30"
              }`}
            >
              {isListening ? (
                <>
                  <span className="absolute -inset-1 rounded-full border-2 border-rose-400/60 animate-pulse" />
                  <MicOff className="h-4 w-4" />
                  <span>Stop Listening</span>
                </>
              ) : (
                <>
                  <Mic className="h-4 w-4" />
                  <span>Start Listening</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={onClearConversation}
              disabled={!hasMessages}
              title="Clear conversation"
              aria-label="Clear conversation"
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span className="hidden md:inline">Clear</span>
            </button>
          </div>
        </div>

        {isSpeaking && (
          <div className="flex items-center justify-center gap-1.5 text-[11px] text-indigo-600 sm:justify-start">
            <Volume2 className="h-3.5 w-3.5 animate-pulse" />
            <span>Playing browser text-to-speech response</span>
          </div>
        )}
      </div>
    </section>
  );
}

export default VoiceControls;
