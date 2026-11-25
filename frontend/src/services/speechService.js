/**
 * Browser Web Speech API (Text-to-Speech) utility service.
 * Uses window.speechSynthesis and SpeechSynthesisUtterance.
 */

let activeUtteranceToken = 0;

export function isSpeechSynthesisSupported() {
  return (
    typeof window !== "undefined" &&
    "speechSynthesis" in window &&
    typeof window.SpeechSynthesisUtterance !== "undefined"
  );
}

export function stopSpeaking() {
  // Invalidate any pending callbacks from prior utterances before cancelling.
  activeUtteranceToken += 1;
  if (!isSpeechSynthesisSupported()) return;
  try {
    window.speechSynthesis.cancel();
  } catch (error) {
    console.error("Failed to stop speech synthesis:", error);
  }
}

export function speakText(
  text,
  { language = "en-IN", muted = false, onStart, onEnd, onError } = {}
) {
  if (muted || !text || !text.trim()) {
    onEnd?.();
    return false;
  }

  if (!isSpeechSynthesisSupported()) {
    onError?.("Text-to-speech is not supported in this browser.");
    return false;
  }

  const token = ++activeUtteranceToken;

  try {
    // Cancel any active or queued speech to prevent overlapping audio.
    window.speechSynthesis.cancel();

    const utterance = new window.SpeechSynthesisUtterance(text);
    utterance.lang = language;
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    // Pick a matching voice when available.
    const voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
      const exactMatch = voices.find((v) => v.lang === language);
      const prefixMatch = voices.find((v) =>
        v.lang.toLowerCase().startsWith(language.split("-")[0].toLowerCase())
      );
      if (exactMatch) {
        utterance.voice = exactMatch;
      } else if (prefixMatch) {
        utterance.voice = prefixMatch;
      }
    }

    utterance.onstart = () => {
      if (token !== activeUtteranceToken) return;
      onStart?.();
    };

    utterance.onend = () => {
      if (token !== activeUtteranceToken) return;
      onEnd?.();
    };

    utterance.onerror = (event) => {
      if (token !== activeUtteranceToken) return;
      if (event?.error === "canceled" || event?.error === "interrupted") {
        onEnd?.();
        return;
      }
      onError?.("Unable to play voice response.");
      onEnd?.();
    };

    window.speechSynthesis.speak(utterance);
    return true;
  } catch (error) {
    console.error("Speech synthesis error:", error);
    if (token === activeUtteranceToken) {
      onError?.("Speech synthesis failed.");
      onEnd?.();
    }
    return false;
  }
}
