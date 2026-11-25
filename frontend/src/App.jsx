import { useCallback, useEffect, useRef, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import AppointmentBooking from "./components/AppointmentBooking";
import AppointmentCalendar from "./components/AppointmentCalendar";
import AppointmentPanel from "./components/AppointmentPanel";
import CRMPanel from "./components/CRMPanel";
import ChatWindow from "./components/ChatWindow";
import Header from "./components/Header";
import KnowledgePanel from "./components/KnowledgePanel";
import LeadPanel from "./components/LeadPanel";
import MessageInput from "./components/MessageInput";
import SentimentPanel from "./components/SentimentPanel";
import VoiceControls from "./components/VoiceControls";
import { useSpeechRecognition } from "./hooks/useSpeechRecognition";
import { fetchAgentSession, sendAgentMessage } from "./services/agentService";
import { fetchAppointments } from "./services/appointmentService";
import { isSpeechSynthesisSupported, speakText, stopSpeaking } from "./services/speechService";

const SESSION_STORAGE_KEY = "fortivex_active_session_id";

function createSessionId() {
  return `session_${Date.now()}`;
}

function getOrInitSessionId() {
  try {
    const existing = window.localStorage.getItem(SESSION_STORAGE_KEY);
    if (existing && existing.trim()) return existing;
    const created = createSessionId();
    window.localStorage.setItem(SESSION_STORAGE_KEY, created);
    return created;
  } catch {
    return createSessionId();
  }
}

function VoiceAgentWorkspace() {
  const [messages, setMessages] = useState([]);
  const [lead, setLead] = useState(null);
  const [sentimentSummary, setSentimentSummary] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [sessionId, setSessionId] = useState(getOrInitSessionId);
  const [language, setLanguage] = useState("en-IN");
  const [isMuted, setIsMuted] = useState(false);
  const [conversationMode, setConversationMode] = useState("push-to-talk");
  const [voiceState, setVoiceState] = useState("idle"); // "idle" | "listening" | "processing" | "speaking" | "error"
  const [activeView, setActiveView] = useState("voice"); // "voice" | "appointments" | "crm"
  const [sidebarTab, setSidebarTab] = useState("lead"); // "lead" | "knowledge" | "sentiment"
  const [appError, setAppError] = useState("");

  const messagesRef = useRef(messages);
  const isProcessingRef = useRef(false);
  const conversationModeRef = useRef(conversationMode);
  const isMutedRef = useRef(isMuted);
  const manualStopRef = useRef(false);
  const resumeTimerRef = useRef(null);
  const startListeningRef = useRef(null);
  const stopListeningRef = useRef(null);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  useEffect(() => {
    conversationModeRef.current = conversationMode;
  }, [conversationMode]);

  useEffect(() => {
    isMutedRef.current = isMuted;
  }, [isMuted]);

  // Restore persisted session context and lead profile on load if available.
  useEffect(() => {
    let active = true;
    fetchAgentSession(sessionId)
      .then((sessionData) => {
        if (!active || !sessionData) return;
        if (sessionData.lead) {
          setLead(sessionData.lead);
        }
        if (sessionData.sentiment_summary) {
          setSentimentSummary(sessionData.sentiment_summary);
        }
        if (Array.isArray(sessionData.messages) && sessionData.messages.length > 0) {
          setMessages(
            sessionData.messages.map((m) => ({
              id: `db-${m.id}`,
              role: m.role,
              content: m.content,
              timestamp: m.created_at,
            }))
          );
        }
      })
      .catch(() => {
        // Ignore initial restore failure if backend is offline; ConnectionStatus shows status.
      });

    return () => {
      active = false;
    };
  }, [sessionId]);

  const refreshAppointments = useCallback(() => {
    fetchAppointments()
      .then((items) => setAppointments(items))
      .catch(() => {});
  }, []);

  useEffect(() => {
    refreshAppointments();
  }, [refreshAppointments]);

  const clearResumeTimer = useCallback(() => {
    if (resumeTimerRef.current) {
      clearTimeout(resumeTimerRef.current);
      resumeTimerRef.current = null;
    }
  }, []);

  const scheduleContinuousListen = useCallback(() => {
    clearResumeTimer();
    if (conversationModeRef.current !== "continuous" || manualStopRef.current) {
      return;
    }
    // Brief delay after TTS ends so speaker audio decays before reopening the mic.
    resumeTimerRef.current = setTimeout(() => {
      resumeTimerRef.current = null;
      if (
        conversationModeRef.current === "continuous" &&
        !manualStopRef.current &&
        !isProcessingRef.current
      ) {
        startListeningRef.current?.();
      }
    }, 250);
  }, [clearResumeTimer]);

  const playAssistantVoice = useCallback(
    (text, { allowAutoResume = true } = {}) => {
      if (isMutedRef.current || !text || !isSpeechSynthesisSupported()) {
        setVoiceState("idle");
        if (allowAutoResume) {
          scheduleContinuousListen();
        }
        return;
      }

      const started = speakText(text, {
        language,
        muted: isMutedRef.current,
        onStart: () => setVoiceState("speaking"),
        onEnd: () => {
          setVoiceState("idle");
          if (allowAutoResume) {
            scheduleContinuousListen();
          }
        },
        onError: (msg) => {
          setAppError(msg);
          setVoiceState("error");
        },
      });

      if (!started) {
        setVoiceState("idle");
      }
    },
    [language, scheduleContinuousListen]
  );

  const handleSendMessage = useCallback(
    async (rawText) => {
      const text = rawText?.trim();
      if (!text || isProcessingRef.current) return;

      clearResumeTimer();
      manualStopRef.current = false;
      isProcessingRef.current = true;
      setAppError("");
      stopListeningRef.current?.();
      stopSpeaking();
      setVoiceState("processing");

      const previousHistory = messagesRef.current;
      const userMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: text,
        timestamp: new Date().toISOString(),
      };

      setMessages([...previousHistory, userMessage]);

      try {
        const reply = await sendAgentMessage({
          message: text,
          sessionId,
          history: previousHistory,
        });
        setMessages((prev) => [...prev, reply]);
        if (reply.lead) {
          setLead(reply.lead);
        }
        if (reply.sentimentSummary) {
          setSentimentSummary(reply.sentimentSummary);
        }
        if (reply.appointment) {
          refreshAppointments();
        }
        isProcessingRef.current = false;
        playAssistantVoice(reply.content, { allowAutoResume: true });
      } catch (err) {
        console.error("Failed to fetch Gemini reply:", err);
        isProcessingRef.current = false;
        setAppError(
          err?.message || "Unable to get a response from the AI assistant. Please try again."
        );
        setVoiceState("error");
      }
    },
    [clearResumeTimer, playAssistantVoice, refreshAppointments, sessionId]
  );

  const handleListeningChange = useCallback((listening) => {
    if (listening) {
      setVoiceState("listening");
    } else if (!isProcessingRef.current) {
      setVoiceState((prev) => (prev === "listening" ? "idle" : prev));
    }
  }, []);

  const canListen = voiceState === "idle" || voiceState === "error";

  const {
    isSupported,
    isListening,
    interimTranscript,
    error: speechError,
    clearError: clearSpeechError,
    startListening,
    stopListening,
  } = useSpeechRecognition({
    language,
    canListen,
    onListeningChange: handleListeningChange,
    onFinalTranscript: handleSendMessage,
  });

  useEffect(() => {
    startListeningRef.current = startListening;
    stopListeningRef.current = stopListening;
  }, [startListening, stopListening]);

  const handleToggleListening = useCallback(() => {
    clearResumeTimer();
    if (isListening) {
      manualStopRef.current = true;
      stopListening();
      setVoiceState("idle");
      return;
    }
    if (voiceState === "processing" || voiceState === "speaking") {
      return;
    }
    manualStopRef.current = false;
    startListening();
  }, [clearResumeTimer, isListening, startListening, stopListening, voiceState]);

  const handleToggleMute = useCallback(() => {
    setIsMuted((prev) => {
      const next = !prev;
      if (next) {
        stopSpeaking();
        setVoiceState((current) => (current === "speaking" ? "idle" : current));
      }
      return next;
    });
  }, []);

  const handleStopSpeaking = useCallback(() => {
    clearResumeTimer();
    manualStopRef.current = true;
    stopSpeaking();
    setVoiceState("idle");
  }, [clearResumeTimer]);

  const handleClearConversation = useCallback(() => {
    clearResumeTimer();
    manualStopRef.current = true;
    stopListening();
    stopSpeaking();
    isProcessingRef.current = false;
    const nextSessionId = createSessionId();
    try {
      window.localStorage.setItem(SESSION_STORAGE_KEY, nextSessionId);
    } catch {
      // Ignore storage errors
    }
    setMessages([]);
    setLead(null);
    setSentimentSummary(null);
    setSessionId(nextSessionId);
    setAppError("");
    clearSpeechError();
    setVoiceState("idle");
  }, [clearResumeTimer, clearSpeechError, stopListening]);

  const handleDismissError = useCallback(() => {
    setAppError("");
    clearSpeechError();
    setVoiceState((prev) => (prev === "error" ? "idle" : prev));
  }, [clearSpeechError]);

  const handleReplaySpeech = useCallback(
    (text) => {
      if (voiceState === "processing" || isListening) return;
      manualStopRef.current = true;
      playAssistantVoice(text, { allowAutoResume: false });
    },
    [isListening, playAssistantVoice, voiceState]
  );

  useEffect(() => {
    return () => {
      clearResumeTimer();
      stopSpeaking();
    };
  }, [clearResumeTimer]);

  const activeError = speechError || appError;
  const isThinking = voiceState === "processing";

  return (
    <div className="flex h-dvh flex-col bg-slate-50 text-slate-900">
      <Header
        language={language}
        onLanguageChange={setLanguage}
        isMuted={isMuted}
        onToggleMute={handleToggleMute}
        activeView={activeView}
        onViewChange={setActiveView}
      />

      {activeView === "crm" ? (
        <main className="flex-1 overflow-y-auto">
          <CRMPanel />
        </main>
      ) : activeView === "appointments" ? (
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-6xl p-4 sm:p-6 space-y-5">
            <AppointmentBooking
              sessionId={sessionId}
              lead={lead}
              onBooked={refreshAppointments}
            />
            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              <AppointmentPanel
                appointments={appointments}
                sessionId={sessionId}
                onUpdated={refreshAppointments}
              />
              <AppointmentCalendar appointments={appointments} />
            </div>
          </div>
        </main>
      ) : (
      <div className="flex flex-1 min-h-0 flex-col lg:flex-row">
        <div className="flex flex-1 min-h-0 flex-col">
          <ChatWindow
            messages={messages}
            isThinking={isThinking}
            error={activeError}
            onDismissError={handleDismissError}
            onSelectPrompt={handleSendMessage}
            onReplaySpeech={handleReplaySpeech}
            isMuted={isMuted}
          />

          <VoiceControls
            isSupported={isSupported}
            voiceState={voiceState}
            conversationMode={conversationMode}
            onConversationModeChange={setConversationMode}
            interimTranscript={interimTranscript}
            hasMessages={messages.length > 0}
            onToggleListening={handleToggleListening}
            onStopSpeaking={handleStopSpeaking}
            onClearConversation={handleClearConversation}
          />

          <MessageInput
            onSendMessage={handleSendMessage}
            isThinking={isThinking}
            isListening={isListening}
            isSpeechSupported={isSupported && voiceState !== "speaking" && !isThinking}
            onToggleListening={handleToggleListening}
          />
        </div>

        <div className="flex flex-col border-t border-slate-200 bg-white lg:w-80 lg:shrink-0 lg:border-t-0 lg:border-l lg:overflow-y-auto">
          <div className="flex border-b border-slate-200 bg-slate-50/70 px-3 pt-2 gap-1">
            <button
              type="button"
              onClick={() => setSidebarTab("lead")}
              className={`rounded-t-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                sidebarTab === "lead"
                  ? "border border-b-0 border-slate-200 bg-white text-indigo-700"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Lead Profile
            </button>
            <button
              type="button"
              onClick={() => setSidebarTab("knowledge")}
              className={`rounded-t-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                sidebarTab === "knowledge"
                  ? "border border-b-0 border-slate-200 bg-white text-indigo-700"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Knowledge
            </button>
            <button
              type="button"
              onClick={() => setSidebarTab("sentiment")}
              className={`rounded-t-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                sidebarTab === "sentiment"
                  ? "border border-b-0 border-slate-200 bg-white text-indigo-700"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Sentiment
            </button>
          </div>

          {sidebarTab === "lead" ? (
            <LeadPanel lead={lead} />
          ) : sidebarTab === "knowledge" ? (
            <KnowledgePanel />
          ) : (
            <SentimentPanel sentimentSummary={sentimentSummary} />
          )}
        </div>
      </div>
      )}
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<VoiceAgentWorkspace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
