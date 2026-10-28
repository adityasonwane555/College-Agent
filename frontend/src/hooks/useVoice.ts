import { useState, useRef, useCallback, useEffect } from 'react';
import { api, API_HOST } from '../services/api';
import type { RobotState } from '../types';

interface UseVoiceOptions {
  onTranscriptionComplete: (text: string) => void;
  onStateChange: (state: RobotState) => void;
  onError: (errMessage: string) => void;
}

export function useVoice({ onTranscriptionComplete, onStateChange, onError }: UseVoiceOptions) {
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [audioInputSource, setAudioInputSourceState] = useState<'robot' | 'laptop'>(() => {
    return (localStorage.getItem('buddy_audio_input_source') as 'robot' | 'laptop') || 'robot';
  });
  const [audioInputDevices, setAudioInputDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedInputDeviceId, setSelectedInputDeviceId] = useState<string>(() => {
    return localStorage.getItem('buddy_audio_input_id') || 'default';
  });
  const [activeMicLabel, setActiveMicLabel] = useState<string>(() => {
    const savedSource = (localStorage.getItem('buddy_audio_input_source') as 'robot' | 'laptop') || 'robot';
    return savedSource === 'robot' ? 'Robot Mic (ESP32 INMP441)' : 'Default Microphone';
  });

  const setAudioInputSource = useCallback((source: 'robot' | 'laptop') => {
    setAudioInputSourceState(source);
    localStorage.setItem('buddy_audio_input_source', source);
    if (source === 'robot') {
      setActiveMicLabel('Robot Mic (ESP32 INMP441)');
    } else {
      setActiveMicLabel('Default Microphone');
    }
  }, []);

  const [audioOutputTarget, setAudioOutputTargetState] = useState<'robot' | 'laptop' | 'both'>(() => {
    const saved = localStorage.getItem('buddy_audio_output_target');
    if (!saved || saved === 'robot') {
      localStorage.setItem('buddy_audio_output_target', 'both');
      return 'both';
    }
    return saved as 'robot' | 'laptop' | 'both';
  });

  const setAudioOutputTarget = useCallback((target: 'robot' | 'laptop' | 'both') => {
    setAudioOutputTargetState(target);
    localStorage.setItem('buddy_audio_output_target', target);
  }, []);

  const lockedVoiceRef = useRef<SpeechSynthesisVoice | null>(null);

  // Enumerate input devices and keep activeMicLabel in sync
  const refreshAudioDevices = useCallback(async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return;
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const inputs = devices.filter((d) => d.kind === 'audioinput');
      setAudioInputDevices(inputs);

      const savedId = localStorage.getItem('buddy_audio_input_id') || 'default';
      if (savedId !== 'default') {
        const match = inputs.find((d) => d.deviceId === savedId);
        if (match && match.label) {
          setActiveMicLabel(match.label);
        } else if (inputs.length > 0 && inputs[0].label) {
          setActiveMicLabel(inputs[0].label);
        }
      } else if (inputs.length > 0 && inputs[0].label) {
        setActiveMicLabel(inputs[0].label);
      }
    } catch (err) {
      console.warn("[Voice] Device enumeration error:", err);
    }
  }, []);

  const changeAudioInputDevice = useCallback((deviceId: string) => {
    setSelectedInputDeviceId(deviceId);
    localStorage.setItem('buddy_audio_input_id', deviceId);
    if (deviceId === 'default') {
      const first = audioInputDevices.find((d) => d.label);
      setActiveMicLabel(first ? `Default (${first.label})` : 'Default Microphone');
    } else {
      const match = audioInputDevices.find((d) => d.deviceId === deviceId);
      if (match && match.label) {
        setActiveMicLabel(match.label);
      }
    }
  }, [audioInputDevices]);

  useEffect(() => {
    refreshAudioDevices();
    if (navigator.mediaDevices && navigator.mediaDevices.addEventListener) {
      navigator.mediaDevices.addEventListener('devicechange', refreshAudioDevices);
      return () => {
        navigator.mediaDevices.removeEventListener('devicechange', refreshAudioDevices);
      };
    }
  }, [refreshAudioDevices]);

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
  const eqIntervalRef = useRef<number | null>(null);
  const audioSafetyTimerRef = useRef<number | null>(null);
  const chunkWatchdogRef = useRef<number | null>(null);
  const speechWatchdogRef = useRef<number | null>(null);

  // Stop current speech playback (optionally preserving state for immediate transitions)
  const stopSpeaking = useCallback((resetState: boolean = true) => {
    if (eqIntervalRef.current) {
      clearInterval(eqIntervalRef.current);
      eqIntervalRef.current = null;
    }
    if (speechHeartbeatRef.current) {
      clearInterval(speechHeartbeatRef.current);
      speechHeartbeatRef.current = null;
    }
    if (audioSafetyTimerRef.current) {
      clearTimeout(audioSafetyTimerRef.current);
      audioSafetyTimerRef.current = null;
    }
    if (chunkWatchdogRef.current) {
      clearTimeout(chunkWatchdogRef.current);
      chunkWatchdogRef.current = null;
    }
    if (speechWatchdogRef.current) {
      clearTimeout(speechWatchdogRef.current);
      speechWatchdogRef.current = null;
    }
    activeUtterancesRef.current = [];
    (window as any).__buddy_active_utterance = null;
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);

    // Immediately abort ESP32 hardware speaker playback
    api.stopVoice(resetState);

    if (resetState) {
      onStateChange('idle');
      api.setLedState('IDLE');
    }
  }, [onStateChange]);

  // Multi-sentence chunked browser speech (prevents Chrome halting at periods/fullstops)
  const fallbackBrowserSpeech = useCallback((text: string) => {
    if (!('speechSynthesis' in window)) return;

    window.speechSynthesis.cancel();
    if (speechHeartbeatRef.current) {
      clearInterval(speechHeartbeatRef.current);
      speechHeartbeatRef.current = null;
    }
    if (chunkWatchdogRef.current) {
      clearTimeout(chunkWatchdogRef.current);
      chunkWatchdogRef.current = null;
    }
    if (speechWatchdogRef.current) {
      clearTimeout(speechWatchdogRef.current);
      speechWatchdogRef.current = null;
    }

    let cleanText = text
      .replace(/[*#_`\[\]~|()[\]{}]/g, ' ')
      .replace(/https?:\/\/\S+/g, '')
      .replace(/\[Source:[^\]]*\]/gi, '')
      .replace(/\s+/g, ' ')
      .trim();

    // Ensure APCOER and institutional acronyms are pronounced letter-by-letter, never as joined words
    cleanText = cleanText
      .replace(/\bA[-.,\s]?P[-.,\s]?C[-.,\s]?O[-.,\s]?E[-.,\s]?R['’]s\b/gi, "A, P, C, O, E, R's")
      .replace(/\bA[-.,\s]?P[-.,\s]?C[-.,\s]?O[-.,\s]?E[-.,\s]?R\b/gi, "A, P, C, O, E, R,")
      .replace(/\bA[-.,\s]?B[-.,\s]?M[-.,\s]?S[-.,\s]?P['’]s\b/gi, "A, B, M, S, P's")
      .replace(/\bA[-.,\s]?B[-.,\s]?M[-.,\s]?S[-.,\s]?P\b/gi, "A, B, M, S, P,")
      .replace(/\bS[-.,\s]?P[-.,\s]?P[-.,\s]?U\b/gi, "S, P, P, U,")
      .replace(/\bD[-.,\s]?T[-.,\s]?E\b/gi, "D, T, E,")
      .replace(/\bA[-.,\s]?I[-.,\s]?C[-.,\s]?T[-.,\s]?E\b/gi, "A, I, C, T, E,")
      .replace(/\bH[-.,\s]?O[-.,\s]?D\b/gi, "H, O, D,")
      .replace(/\bT[-.,\s]?P[-.,\s]?O\b/gi, "T, P, O,")
      .replace(/,\s*,+/g, ',')
      .replace(/\s+,/g, ',')
      .replace(/,\s*([.!?:;])/g, '$1')
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

    // Trigger SPEAKING state on hardware LED immediately when speech playback starts
    setIsSpeaking(true);
    onStateChange('speaking');
    api.setLedState('SPEAKING');

    // Chromium keep-alive heartbeat: Prevents speech engine pause after fullstop
    speechHeartbeatRef.current = window.setInterval(() => {
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      }
    }, 3000);

    const finishSpeech = () => {
      if (speechHeartbeatRef.current) {
        clearInterval(speechHeartbeatRef.current);
        speechHeartbeatRef.current = null;
      }
      if (chunkWatchdogRef.current) {
        clearTimeout(chunkWatchdogRef.current);
        chunkWatchdogRef.current = null;
      }
      if (speechWatchdogRef.current) {
        clearTimeout(speechWatchdogRef.current);
        speechWatchdogRef.current = null;
      }
      activeUtterancesRef.current = [];
      (window as any).__buddy_active_utterance = null;
      setIsSpeaking(false);
      // Clean, smiling transition before returning to idle
      onStateChange('happy');
      api.setLedState('IDLE');
      setTimeout(() => {
        onStateChange('idle');
      }, 1800);
    };

    // Overall speech safety timer (prevents speech hanging indefinitely under any circumstance)
    const overallSafetyMs = Math.max(cleanText.length * 200, 15000) + 30000;
    speechWatchdogRef.current = window.setTimeout(() => {
      if (!isCanceled) {
        console.warn("[Browser Speech] Overall speech safety timer triggered, safely finishing.");
        isCanceled = true;
        finishSpeech();
      }
    }, overallSafetyMs);

    const speakChunk = (idx: number) => {
      if (isCanceled || idx >= sentences.length) {
        finishSpeech();
        return;
      }

      const utterance = new SpeechSynthesisUtterance(sentences[idx]);
      utterance.rate = 1.02;
      utterance.pitch = 1.12;
      if (voiceToUse) {
        utterance.voice = voiceToUse;
      }

      // Pin utterance to global object to prevent Chromium V8 GC from dropping onend event
      (window as any).__buddy_active_utterance = utterance;
      activeUtterancesRef.current.push(utterance);

      // Per-chunk watchdog: generous timeout preventing premature cuts
      const chunkTimeoutMs = Math.max(sentences[idx].length * 200, 6000) + 15000;
      if (chunkWatchdogRef.current) {
        clearTimeout(chunkWatchdogRef.current);
      }
      chunkWatchdogRef.current = window.setTimeout(() => {
        console.warn(`[Browser Speech] Watchdog timeout for chunk ${idx}, auto-advancing.`);
        if (!isCanceled) {
          currentIndex++;
          speakChunk(currentIndex);
        }
      }, chunkTimeoutMs);

      utterance.onend = () => {
        if (chunkWatchdogRef.current) {
          clearTimeout(chunkWatchdogRef.current);
          chunkWatchdogRef.current = null;
        }
        if (!isCanceled) {
          currentIndex++;
          speakChunk(currentIndex);
        }
      };

      utterance.onerror = (e) => {
        console.warn("[Browser Speech] Chunk speech error:", e);
        if (chunkWatchdogRef.current) {
          clearTimeout(chunkWatchdogRef.current);
          chunkWatchdogRef.current = null;
        }
        if (!isCanceled) {
          currentIndex++;
          speakChunk(currentIndex);
        }
      };

      window.speechSynthesis.speak(utterance);
    };

    setTimeout(() => {
      window.speechSynthesis.resume();
      speakChunk(0);
    }, 50);
  }, [onStateChange]);

  const isEsp32RecordingRef = useRef(false);

  // Start Push-To-Talk Recording
  const startRecording = useCallback(async () => {
    // Stop any ongoing playback without dropping state to IDLE
    stopSpeaking(false);

    // Robot Mic (ESP32 INMP441 I2S Digital Mic over Wi-Fi)
    if (audioInputSource === 'robot') {
      if (isEsp32RecordingRef.current) return;
      isEsp32RecordingRef.current = true;
      setIsRecording(true);
      onStateChange('listening');
      api.setLedState('LISTENING');

      try {
        console.log("[useVoice] Capturing audio from ESP32 INMP441 microphone over Wi-Fi (4s)...");
        const result = await api.recordEsp32Mic(4);
        isEsp32RecordingRef.current = false;
        setIsRecording(false);

        if (result.success && result.text && result.text.trim().length > 0) {
          console.log("[useVoice] ESP32 mic transcription received:", result.text);
          onStateChange('thinking');
          api.setLedState('THINKING');
          onTranscriptionComplete(result.text.trim());
        } else {
          console.warn("[useVoice] No speech detected from robot mic:", result);
          onError(result.error || "No speech detected from robot microphone. Please speak clearly towards the robot's microphone.");
          onStateChange('idle');
          api.setLedState('IDLE');
        }
      } catch (err: any) {
        isEsp32RecordingRef.current = false;
        setIsRecording(false);
        console.error("[useVoice] ESP32 mic recording error:", err);
        onError(`Robot Mic Error: ${err.message || 'Failed to capture audio from robot microphone'}. Check that ESP32 is online.`);
        onStateChange('error');
        api.setLedState('ERROR');
      }
      return;
    }

    // Laptop WebRTC Microphone Fallback
    try {
      const savedMicId = localStorage.getItem('buddy_audio_input_id') || selectedInputDeviceId;
      const audioConstraints: MediaTrackConstraints = (savedMicId && savedMicId !== 'default')
        ? { deviceId: { exact: savedMicId } }
        : {};

      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: audioConstraints });
      } catch (err) {
        console.warn("[Voice] Exact mic constraint failed, falling back to default:", err);
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      }

      // Update actual active microphone label from active track
      const audioTrack = stream.getAudioTracks()[0];
      if (audioTrack && audioTrack.label) {
        setActiveMicLabel(audioTrack.label);
      }
      refreshAudioDevices();

      audioChunksRef.current = [];

      // Determine the best supported mimeType across Chrome, Edge, Firefox, Safari
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        if (MediaRecorder.isTypeSupported('audio/webm')) {
          mimeType = 'audio/webm';
        } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
          mimeType = 'audio/ogg;codecs=opus';
        } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
          mimeType = 'audio/mp4';
        } else {
          mimeType = '';
        }
      }

      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        // Stop audio tracks to release microphone hardware immediately
        stream.getTracks().forEach((track) => track.stop());
        setIsRecording(false);

        if (audioChunksRef.current.length === 0) {
          console.warn("[Voice] No audio chunks captured by microphone.");
          onError("No audio detected. Please check your microphone connection and speak clearly.");
          onStateChange('idle');
          api.setLedState('IDLE');
          return;
        }

        const effectiveMimeType = recorder.mimeType || mimeType || 'audio/webm';
        const audioBlob = new Blob(audioChunksRef.current, { type: effectiveMimeType });
        console.log(`[Voice] Audio captured: ${audioBlob.size} bytes (${effectiveMimeType})`);

        try {
          onStateChange('thinking' as any);
          api.setLedState('THINKING');
          const result = await api.transcribeAudio(audioBlob);
          if (result.success && result.text) {
            onTranscriptionComplete(result.text);
          } else {
            onError(result.error || "No speech detected in recording.");
            onStateChange('idle');
            api.setLedState('IDLE');
          }
        } catch (err: any) {
          onError(err.message || "Failed to transcribe audio.");
          onStateChange('error');
          api.setLedState('ERROR');
        }
      };

      // Crucial: Pass 100ms timeslice so ondataavailable continuously buffers audio chunks
      recorder.start(100);
      setIsRecording(true);
      onStateChange('listening');
      api.setLedState('LISTENING');
    } catch (err: any) {
      setIsRecording(false);
      onStateChange('error');
      api.setLedState('ERROR');
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        onError("Microphone access was denied. Please allow microphone permissions in your browser address bar.");
      } else {
        onError(`Microphone error: ${err.message || err.name}`);
      }
    }
  }, [audioInputSource, onStateChange, onTranscriptionComplete, onError, stopSpeaking, selectedInputDeviceId, refreshAudioDevices]);

  // Stop Recording
  const stopRecording = useCallback(() => {
    if (audioInputSource === 'robot') {
      // Timed clip from ESP32 finishes automatically
      return;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  }, [audioInputSource]);

  // Play assistant voice
  const speak = useCallback(async (text: string, audioUrl?: string) => {
    if (isMuted) return;

    // Stop and clear previous playback without dropping to IDLE state
    if (eqIntervalRef.current) {
      clearInterval(eqIntervalRef.current);
      eqIntervalRef.current = null;
    }
    if (speechHeartbeatRef.current) {
      clearInterval(speechHeartbeatRef.current);
      speechHeartbeatRef.current = null;
    }
    if (audioSafetyTimerRef.current) {
      clearTimeout(audioSafetyTimerRef.current);
      audioSafetyTimerRef.current = null;
    }
    if (chunkWatchdogRef.current) {
      clearTimeout(chunkWatchdogRef.current);
      chunkWatchdogRef.current = null;
    }
    if (speechWatchdogRef.current) {
      clearTimeout(speechWatchdogRef.current);
      speechWatchdogRef.current = null;
    }
    activeUtterancesRef.current = [];
    (window as any).__buddy_active_utterance = null;
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }

    // Immediately enter SPEAKING state on UI face and hardware LED
    setIsSpeaking(true);
    onStateChange('speaking');
    api.setLedState('SPEAKING', 0.8);

    // Helper to play WAV/MP3 audio element
    const playAudioUrl = async (url: string) => {
      const fullUrl = `http://${API_HOST}:8000${url}`;
      const outputTarget = (localStorage.getItem('buddy_audio_output_target') as 'robot' | 'laptop' | 'both') || 'both';
      console.log(`[Voice] Playing audio (${outputTarget} destination):`, fullUrl);
      const audio = new Audio(fullUrl);
      
      // When 'robot' is selected, mute the local laptop audio element.
      // If 'laptop' or 'both' (default) is selected, play at full volume (1.0).
      audio.volume = outputTarget === 'robot' ? 0.0 : 1.0;
      const savedSinkId = localStorage.getItem('buddy_audio_output_id');
      if (savedSinkId && savedSinkId !== 'default' && 'setSinkId' in HTMLMediaElement.prototype) {
        try {
          await (audio as any).setSinkId(savedSinkId);
        } catch (e) {
          console.warn("[Voice] Could not set audio output sink:", e);
        }
      }
      currentAudioRef.current = audio;

      const armSafetyTimer = () => {
        const durationSec = (audio.duration && !isNaN(audio.duration) && isFinite(audio.duration) && audio.duration > 0)
          ? audio.duration
          : Math.max(text.length * 0.20, 8.0);
        // Generous buffer: actual duration + 25 seconds of grace period
        const safetyMs = (durationSec * 1000) + 25000;

        if (audioSafetyTimerRef.current) {
          clearTimeout(audioSafetyTimerRef.current);
        }
        audioSafetyTimerRef.current = window.setTimeout(() => {
          if (currentAudioRef.current === audio && !audio.paused && !audio.ended) {
            // If audio is actively still progressing, don't interrupt it!
            if (audio.duration && !isNaN(audio.duration) && audio.currentTime < (audio.duration - 0.75)) {
              console.log("[Voice] Audio still progressing smoothly, re-arming watchdog.");
              armSafetyTimer();
              return;
            }
            console.warn("[Voice] Audio safety watchdog fired after full playback grace period.");
            currentAudioRef.current = null;
            setIsSpeaking(false);
            onStateChange('happy');
            api.setLedState('IDLE');
            setTimeout(() => onStateChange('idle'), 1800);
          }
        }, safetyMs);
      };

      audio.onloadedmetadata = () => {
        armSafetyTimer();
      };

      // Audio playback start: Confirm and sustain SPEAKING state
      audio.onplay = () => {
        setIsSpeaking(true);
        onStateChange('speaking');
        api.setLedState('SPEAKING', 0.8);
        armSafetyTimer();
      };

      // Audio playback completion: Transition hardware to IDLE with cheerful happy smile
      audio.onended = () => {
        if (audioSafetyTimerRef.current) {
          clearTimeout(audioSafetyTimerRef.current);
          audioSafetyTimerRef.current = null;
        }
        if (eqIntervalRef.current) {
          clearInterval(eqIntervalRef.current);
          eqIntervalRef.current = null;
        }
        setIsSpeaking(false);
        currentAudioRef.current = null;
        onStateChange('happy');
        api.setLedState('IDLE');
        setTimeout(() => {
          onStateChange('idle');
        }, 1800);
      };

      audio.onerror = (e) => {
        console.warn("[Voice] Audio element failed to play, switching to browser speech:", e);
        if (audioSafetyTimerRef.current) {
          clearTimeout(audioSafetyTimerRef.current);
          audioSafetyTimerRef.current = null;
        }
        setIsSpeaking(false);
        onStateChange('idle');
        fallbackBrowserSpeech(text);
      };

      try {
        await audio.play();
      } catch (err) {
        console.warn("[Voice] audio.play() rejected (autoplay policy), switching to browser speech:", err);
        if (audioSafetyTimerRef.current) {
          clearTimeout(audioSafetyTimerRef.current);
          audioSafetyTimerRef.current = null;
        }
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
    // Disabled: Prevents premature SPEAKING LED overrides while AI orchestrator is thinking
  }, []);

  return {
    isRecording,
    isSpeaking,
    isMuted,
    toggleMute: () => setIsMuted(prev => !prev),
    startRecording,
    stopRecording,
    stopSpeaking,
    speak,
    playInstantAcknowledgment,
    audioInputDevices,
    selectedInputDeviceId,
    changeAudioInputDevice,
    activeMicLabel,
    refreshAudioDevices,
    audioOutputTarget,
    setAudioOutputTarget,
    audioInputSource,
    setAudioInputSource
  };
}
