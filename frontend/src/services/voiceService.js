/**
 * Browser Web Speech API (Speech-to-Text) utility service.
 */

export const SUPPORTED_LANGUAGES = [
  { code: "en-IN", label: "English (India)" },
  { code: "hi-IN", label: "Hindi (India)" },
];

export function getSpeechRecognitionConstructor() {
  if (typeof window === "undefined") return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

export function isSpeechRecognitionSupported() {
  return Boolean(getSpeechRecognitionConstructor());
}

export function mapSpeechErrorToMessage(errorCode) {
  switch (errorCode) {
    case "not-allowed":
    case "service-not-allowed":
      return "Microphone permission was denied. Please allow microphone access in your browser settings and try again.";
    case "audio-capture":
      return "No microphone was found. Please connect a microphone and try again.";
    case "no-speech":
      return "No speech was detected. Please try speaking clearly into your microphone.";
    case "network":
      return "A network error occurred during speech recognition. Please check your connection.";
    case "language-not-supported":
      return "The selected language is not supported by your browser's speech recognition engine.";
    case "aborted":
      return "";
    default:
      return "Speech recognition encountered an unexpected error. You can still type your message below.";
  }
}

export function createSpeechRecognition({
  language = "en-IN",
  continuous = true,
  interimResults = true,
} = {}) {
  const SpeechRecognition = getSpeechRecognitionConstructor();
  if (!SpeechRecognition) {
    return null;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = language;
  recognition.continuous = continuous;
  recognition.interimResults = interimResults;
  recognition.maxAlternatives = 1;

  return recognition;
}
