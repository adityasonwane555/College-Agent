import { useState, useRef, useCallback, useEffect } from 'react';
import { api, API_HOST } from '../services/api';

interface UseVoiceOptions {
  onTranscriptionComplete: (text: string) => void;
  onStateChange: (state: 'listening' | 'speaking' | 'idle' | 'error') => void;
  onError: (errMessage: string) => void;
}

export function useVoice({ onTranscriptionComplete, onStateChange, onError }: UseVoiceOptions) {
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const lockedVoiceRef = useRef<SpeechSynthesisVoice | null>(null);

  // Pre-load and strictly lock the assistant's voice persona on mount
  useEffect(() => {
    if (!('speechSynthesis' in window)) return;

    const findFemaleVoice = () => {
      const voices = window.speechSynthesis.getVoices();
      if (!voices || voices.length === 0) return;

      // Priority 1: Known natural feminine voices
      const priorityMatch = voices.find(v =>
        /zira|jenny|aria|samantha|female|katherine|susan|victoria/i.test(v.name)
      );
      // Priority 2: Any English voice that is NOT an explicit male voice
      const genericMatch = voices.find(v =>
        v.lang.startsWith('en') && !/david|george|mark|male|guy|man|james|richard|ravi/i.test(v.name)
      );

      lockedVoiceRef.current = priorityMatch || genericMatch || voices[0] || null;
      if (lockedVoiceRef.current) {
        console.log("[useVoice] Locked assistant fallback voice:", lockedVoiceRef.current.name);
      }
    };

    findFemaleVoice();
    window.speechSynthesis.onvoiceschanged = findFemaleVoice;
    return () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.onvoiceschanged = null;
      }
    };
  }, []);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const activeUtterancesRef = useRef<SpeechSynthesisUtterance[]>([]);
  const speechHeartbeatRef = useRef<number | null>(null);

  // Start Push-To-Talk Recording
  const startRecording = useCallback(async () => {
    // Stop any ongoing playback
    stopSpeaking();

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];

      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        // Stop audio tracks
        stream.getTracks().forEach((track) => track.stop());
        setIsRecording(false);

        if (audioChunksRef.current.length === 0) {
          onStateChange('idle');
          return;
        }

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        try {
          onStateChange('thinking' as any);
          const result = await api.transcribeAudio(audioBlob);
          if (result.success && result.text) {
            onTranscriptionComplete(result.text);
          } else {
            onError(result.error || "No speech detected in recording.");
            onStateChange('idle');
          }
        } catch (err: any) {
          onError(err.message || "Failed to transcribe audio.");
          onStateChange('error');
        }
      };

      recorder.start();
      setIsRecording(true);
      onStateChange('listening');
    } catch (err: any) {
      setIsRecording(false);
      onStateChange('error');
      if (err.name === 'NotAllowedError') {
        onError("Microphone access was denied. Please allow microphone permissions in your browser.");
      } else {
        onError(`Microphone error: ${err.message}`);
      }
    }
  }, [onStateChange, onTranscriptionComplete, onError]);

  // Stop Recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  }, []);

  // Stop current speech playback
  const stopSpeaking = useCallback(() => {
    if (speechHeartbeatRef.current) {
      clearInterval(speechHeartbeatRef.current);
      speechHeartbeatRef.current = null;
    }
    activeUtterancesRef.current = [];
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  }, []);

  // Multi-sentence chunked browser speech (prevents Chrome halting at periods/fullstops)
  const fallbackBrowserSpeech = useCallback((text: string) => {
    if (!('speechSynthesis' in window)) return;

    window.speechSynthesis.cancel();
    if (speechHeartbeatRef.current) {
      clearInterval(speechHeartbeatRef.current);
      speechHeartbeatRef.current = null;
    }

    const cleanText = text
      .replace(/[*#_`\[\]~|]/g, '')
      .replace(/https?:\/\/\S+/g, '')
      .replace(/\[Source:[^\]]*\]/gi, '')
      .replace(/\s+/g, ' ')
      .trim();

    if (!cleanText) return;

    // Split text into distinct sentences so Chromium never pauses or truncates at fullstops
    const rawChunks = cleanText.match(/[^.!?]+[.!?]+|\s*[^.!?]+$/g) || [cleanText];
    const sentences = rawChunks.map(s => s.trim()).filter(s => s.length > 0);
    if (sentences.length === 0) return;

    // Strictly lock to female/youthful assistant voice
    let voiceToUse = lockedVoiceRef.current;
    if (!voiceToUse) {
      const availableVoices = window.speechSynthesis.getVoices();
      voiceToUse = availableVoices.find(v => 
        /zira|jenny|aria|samantha|female|katherine|susan|victoria/i.test(v.name)
      ) || availableVoices.find(v => 
        v.lang.startsWith('en') && !/david|george|mark|male|guy|man|james|richard|ravi/i.test(v.name)
      ) || null;
      if (voiceToUse) {
        lockedVoiceRef.current = voiceToUse;
      }
    }

    activeUtterancesRef.current = [];
    let currentIndex = 0;
    let isCanceled = false;

    setIsSpeaking(true);
    onStateChange('speaking');

    // Chromium keep-alive heartbeat: Prevents speech engine pause after fullstop
    speechHeartbeatRef.current = window.setInterval(() => {
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      }
    }, 4000);

    const speakChunk = (idx: number) => {
      if (isCanceled || idx >= sentences.length) {
        if (speechHeartbeatRef.current) {
          clearInterval(speechHeartbeatRef.current);
          speechHeartbeatRef.current = null;
        }
        activeUtterancesRef.current = [];
        setIsSpeaking(false);
        onStateChange('idle');
        return;
      }

      const utterance = new SpeechSynthesisUtterance(sentences[idx]);
      utterance.rate = 1.02;
      utterance.pitch = 1.12;
      if (voiceToUse) {
        utterance.voice = voiceToUse;
      }

      activeUtterancesRef.current.push(utterance);

      utterance.onend = () => {
        if (!isCanceled) {
          currentIndex++;
          speakChunk(currentIndex);
        }
      };

      utterance.onerror = (e) => {
        console.warn("[Browser Speech] Chunk speech error:", e);
        if (!isCanceled) {
          currentIndex++;
          speakChunk(currentIndex);
        }
      };

      window.speechSynthesis.speak(utterance);
    };

    speakChunk(0);
  }, [onStateChange]);

  // Play assistant voice
  const speak = useCallback(async (text: string, audioUrl?: string) => {
    if (isMuted) return;
    stopSpeaking();

    // Helper to play WAV/MP3 audio element
    const playAudioUrl = async (url: string) => {
      const fullUrl = `http://${API_HOST}:8000${url}`;
      console.log("[Voice] Loading audio from:", fullUrl);
      const audio = new Audio(fullUrl);
      currentAudioRef.current = audio;

      audio.onplay = () => {
        setIsSpeaking(true);
        onStateChange('speaking');
      };

      audio.onended = () => {
        setIsSpeaking(false);
        currentAudioRef.current = null;
        onStateChange('idle');
      };

      audio.onerror = (e) => {
        console.warn("[Voice] Audio element failed to play, switching to browser speech:", e);
        setIsSpeaking(false);
        onStateChange('idle');
        fallbackBrowserSpeech(text);
      };

      try {
        await audio.play();
      } catch (err) {
        console.warn("[Voice] audio.play() rejected (autoplay policy), switching to browser speech:", err);
        setIsSpeaking(false);
        onStateChange('idle');
        fallbackBrowserSpeech(text);
      }
    };

    // 1. If pre-generated audio URL is provided
    if (audioUrl) {
      try {
        await playAudioUrl(audioUrl);
        return;
      } catch (err) {
        console.warn("Direct audio playback failed:", err);
      }
    }

    // 2. Asynchronously request synthesis from backend
    try {
      const synthRes = await api.synthesizeSpeech(text);
      if (synthRes && synthRes.audio_url) {
        console.log("[Voice] Neural audio ready:", synthRes.audio_url);
        await playAudioUrl(synthRes.audio_url);
        return;
      } else {
        fallbackBrowserSpeech(text);
        return;
      }
    } catch (err) {
      console.warn("Async synthesis request failed, using browser speech fallback:", err);
      fallbackBrowserSpeech(text);
    }
  }, [isMuted, stopSpeaking, onStateChange, fallbackBrowserSpeech]);

  const playInstantAcknowledgment = useCallback(() => {
    if (isMuted || !('speechSynthesis' in window)) return;
    const fillers = [
      "Looking into that for you!",
      "Checking the college records...",
      "One moment, let me find that!",
      "Looking that up right now!"
    ];
    const phrase = fillers[Math.floor(Math.random() * fillers.length)];
    const utterance = new SpeechSynthesisUtterance(phrase);
    utterance.rate = 1.1;
    utterance.pitch = 1.15;
    if (lockedVoiceRef.current) {
      utterance.voice = lockedVoiceRef.current;
    }
    window.speechSynthesis.speak(utterance);
  }, [isMuted]);

  return {
    isRecording,
    isSpeaking,
    isMuted,
    toggleMute: () => setIsMuted(prev => !prev),
    startRecording,
    stopRecording,
    stopSpeaking,
    speak,
    playInstantAcknowledgment
  };
}
