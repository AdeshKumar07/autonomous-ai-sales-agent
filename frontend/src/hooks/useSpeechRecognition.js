import { useCallback, useEffect, useRef, useState } from "react";
import {
  createSpeechRecognition,
  isSpeechRecognitionSupported,
  mapSpeechErrorToMessage,
} from "../services/voiceService";

export function useSpeechRecognition({
  language = "en-IN",
  canListen = true,
  onListeningChange,
  onFinalTranscript,
} = {}) {
  const isSupported = isSpeechRecognitionSupported();
  const [isListening, setIsListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState("");
  const [error, setError] = useState("");

  const recognitionRef = useRef(null);
  const isTransitioningRef = useRef(false);
  const userStoppedRef = useRef(false);
  const hasSubmittedRef = useRef(false);
  const canListenRef = useRef(canListen);
  const onListeningChangeRef = useRef(onListeningChange);
  const onFinalTranscriptRef = useRef(onFinalTranscript);

  useEffect(() => {
    canListenRef.current = canListen;
  }, [canListen]);

  useEffect(() => {
    onListeningChangeRef.current = onListeningChange;
  }, [onListeningChange]);

  useEffect(() => {
    onFinalTranscriptRef.current = onFinalTranscript;
  }, [onFinalTranscript]);

  const clearError = useCallback(() => {
    setError("");
  }, []);

  const stopListening = useCallback(() => {
    userStoppedRef.current = true;
    const recognition = recognitionRef.current;
    if (!recognition) {
      setIsListening(false);
      setInterimTranscript("");
      isTransitioningRef.current = false;
      onListeningChangeRef.current?.(false);
      return;
    }

    isTransitioningRef.current = true;
    try {
      recognition.stop();
    } catch {
      recognitionRef.current = null;
      setIsListening(false);
      setInterimTranscript("");
      isTransitioningRef.current = false;
      onListeningChangeRef.current?.(false);
    }
  }, []);

  const startListening = useCallback(() => {
    if (!isSupported) {
      setError(
        "Speech recognition is not supported in this browser. Please use Chrome or Edge, or type your message below."
      );
      return;
    }

    // Do not start if state machine disallows listening or a session is active/transitioning.
    if (
      !canListenRef.current ||
      isListening ||
      isTransitioningRef.current ||
      recognitionRef.current
    ) {
      return;
    }

    setError("");
    setInterimTranscript("");
    userStoppedRef.current = false;
    hasSubmittedRef.current = false;
    isTransitioningRef.current = true;

    const recognition = createSpeechRecognition({
      language,
      continuous: false,
      interimResults: true,
    });

    if (!recognition) {
      isTransitioningRef.current = false;
      setError("Speech recognition could not be initialized in this browser.");
      return;
    }

    recognition.onstart = () => {
      if (recognitionRef.current !== recognition) return;
      isTransitioningRef.current = false;
      setIsListening(true);
      onListeningChangeRef.current?.(true);
    };

    recognition.onresult = (event) => {
      if (recognitionRef.current !== recognition || hasSubmittedRef.current) {
        return;
      }

      let interim = "";
      let finalChunk = "";

      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        const transcriptText = result[0]?.transcript ?? "";
        if (result.isFinal) {
          finalChunk += transcriptText;
        } else {
          interim += transcriptText;
        }
      }

      setInterimTranscript(interim.trim());

      const cleanedFinal = finalChunk.trim();
      if (cleanedFinal) {
        // Lock and stop recognition immediately so TTS playback cannot be captured.
        hasSubmittedRef.current = true;
        userStoppedRef.current = true;
        setInterimTranscript("");
        setIsListening(false);
        onListeningChangeRef.current?.(false);

        try {
          recognition.stop();
        } catch {
          // Ignore stop errors if already ending
        }

        onFinalTranscriptRef.current?.(cleanedFinal);
      }
    };

    recognition.onerror = (event) => {
      if (recognitionRef.current !== recognition) return;
      isTransitioningRef.current = false;

      if (event.error === "aborted" && userStoppedRef.current) {
        return;
      }

      const friendlyMessage = mapSpeechErrorToMessage(event.error);
      if (friendlyMessage) {
        setError(friendlyMessage);
      }

      setIsListening(false);
      setInterimTranscript("");
      recognitionRef.current = null;
      onListeningChangeRef.current?.(false);
    };

    recognition.onend = () => {
      if (recognitionRef.current !== recognition) return;
      isTransitioningRef.current = false;
      recognitionRef.current = null;
      setIsListening(false);
      setInterimTranscript("");
      onListeningChangeRef.current?.(false);
    };

    recognitionRef.current = recognition;

    try {
      recognition.start();
    } catch (err) {
      console.error("Failed to start speech recognition:", err);
      recognitionRef.current = null;
      isTransitioningRef.current = false;
      setIsListening(false);
      onListeningChangeRef.current?.(false);
      setError("Could not start microphone listening. Please try again.");
    }
  }, [isListening, isSupported, language]);

  const toggleListening = useCallback(() => {
    if (isListening || recognitionRef.current) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  // Stop active recognition if language changes so the next session uses the new language.
  useEffect(() => {
    if (recognitionRef.current) {
      stopListening();
    }
  }, [language, stopListening]);

  // Cleanup on unmount.
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        userStoppedRef.current = true;
        try {
          recognitionRef.current.abort();
        } catch {
          // Ignore cleanup errors
        }
        recognitionRef.current = null;
      }
    };
  }, []);

  return {
    isSupported,
    isListening,
    interimTranscript,
    error,
    clearError,
    startListening,
    stopListening,
    toggleListening,
  };
}
