/**
 * BUDDY AI — useVoice Custom React Hook
 * Manages audio lifecycle, dual-microphone routing (ESP32 INMP441 vs local device),
 * speech recognition transcription, speech synthesis playback, and active cancellation.
 */

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
  // Audio Input Routing: defaults to 'laptop' for instant browser capture, with automated
  // fallback if the ESP32 INMP441 physical robot microphone is unreachable.
  const [audioInputSource, setAudioInputSourceState] = useState<'robot' | 'laptop'>(() => {
    return (localStorage.getItem('buddy_audio_input_source') as 'robot' | 'laptop') || 'laptop';
  });
  const [audioInputDevices, setAudioInputDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedInputDeviceId, setSelectedInputDeviceId] = useState<string>(() => {
    return localStorage.getItem('buddy_audio_input_id') || 'default';
  });
  const [activeMicLabel, setActiveMicLabel] = useState<string>(() => {
    const savedSource = (localStorage.getItem('buddy_audio_input_source') as 'robot' | 'laptop') || 'laptop';
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

  // Audio Output Routing: defaults to 'both' to guarantee audible playback through both
  // laptop/browser speakers and the physical ESP32 MAX98357A speaker simultaneously.
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
  const activeAudiosRef = useRef<Set<HTMLAudioElement>>(new Set());
  const activeUtterancesRef = useRef<SpeechSynthesisUtterance[]>([]);
  const speechHeartbeatRef = useRef<number | null>(null);
  const eqIntervalRef = useRef<number | null>(null);
  const audioSafetyTimerRef = useRef<number | null>(null);
  const chunkWatchdogRef = useRef<number | null>(null);
  const speechWatchdogRef = useRef<number | null>(null);
  const transitionTimerRef = useRef<number | null>(null);
  const speechGenerationIdRef = useRef<number>(0);
  const isCanceledRef = useRef<boolean>(false);

  const clearAllVoiceTimers = useCallback(() => {
    if (transitionTimerRef.current) {
      clearTimeout(transitionTimerRef.current);
      transitionTimerRef.current = null;
    }
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
  }, []);

  // Stop current speech playback and synchronously align UI and hardware state
  const stopSpeaking = useCallback((targetStateOrReset: boolean | RobotState = 'idle') => {
    speechGenerationIdRef.current++;
    isCanceledRef.current = true;
    clearAllVoiceTimers();

    activeUtterancesRef.current = [];
    (window as any).__buddy_active_utterance = null;

    // 1. Immediately mute and halt ALL active Audio elements tracked in registry
    activeAudiosRef.current.forEach((a) => {
      try {
        a.pause();
        a.muted = true;
        a.volume = 0;
        a.currentTime = 0;
        a.onplay = null;
        a.onended = null;
        a.onerror = null;
        a.onloadedmetadata = null;
        a.src = '';
      } catch {}
    });
    activeAudiosRef.current.clear();

    if (currentAudioRef.current) {
      const a = currentAudioRef.current;
      a.onplay = null;
      a.onended = null;
      a.onerror = null;
      a.onloadedmetadata = null;
      try {
        a.pause();
        a.muted = true;
        a.volume = 0;
        a.currentTime = 0;
        a.src = '';
      } catch {}
      currentAudioRef.current = null;
    }

    // 2. Mute and stop any audio element present in the document
    if (typeof document !== 'undefined') {
      try {
        document.querySelectorAll('audio').forEach((el) => {
          try {
            el.pause();
            el.muted = true;
            el.volume = 0;
            el.currentTime = 0;
          } catch {}
        });
      } catch {}
    }

    // 3. Immediately halt browser speech synthesis in Chromium/WebKit on Windows
    if ('speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
        // Speak zero-length silent utterance to flush Chromium's Windows SAPI audio buffer
        const silentUtterance = new SpeechSynthesisUtterance('');
        silentUtterance.volume = 0;
        window.speechSynthesis.speak(silentUtterance);
        window.speechSynthesis.cancel();
        window.speechSynthesis.pause();
        window.speechSynthesis.cancel();
      } catch {}
    }

    setIsSpeaking(false);

    let targetState: RobotState = 'idle';
    if (typeof targetStateOrReset === 'string') {
      targetState = targetStateOrReset;
    } else if (targetStateOrReset === false) {
      targetState = 'idle';
    }

    // Immediately abort ESP32 hardware speaker playback and synchronize state
    api.stopVoice(targetState.toUpperCase());
    onStateChange(targetState);
    api.setLedState(targetState.toUpperCase());
  }, [clearAllVoiceTimers, onStateChange]);

  // Multi-sentence chunked browser speech (prevents Chrome halting at periods/fullstops)
  const fallbackBrowserSpeech = useCallback((text: string, genId?: number) => {
    if (!('speechSynthesis' in window)) return;
    const currentGen = genId !== undefined ? genId : speechGenerationIdRef.current;
    if (speechGenerationIdRef.current !== currentGen || isCanceledRef.current) return;

    clearAllVoiceTimers();
    try {
      window.speechSynthesis.cancel();
    } catch {}

    let cleanText = text
      .replace(/[*#_`\[\]~|()[\]{}]/g, ' ')
      .replace(/https?:\/\/\S+/g, '')
      .replace(/\[Source:[^\]]*\]/gi, '')
      .replace(/\s+/g, ' ')
      .trim();

    // Preserve clean acronyms without awkward comma breaks in browser speech
    cleanText = cleanText
      .replace(/\bA[-.,\s]?P[-.,\s]?C[-.,\s]?O[-.,\s]?E[-.,\s]?R['’]s\b/gi, "APCOER's")
      .replace(/\bA[-.,\s]?P[-.,\s]?C[-.,\s]?O[-.,\s]?E[-.,\s]?R\b/gi, "APCOER")
      .replace(/\bA[-.,\s]?B[-.,\s]?M[-.,\s]?S[-.,\s]?P['’]s\b/gi, "ABMSP's")
      .replace(/\bA[-.,\s]?B[-.,\s]?M[-.,\s]?S[-.,\s]?P\b/gi, "ABMSP")
      .replace(/\bS[-.,\s]?P[-.,\s]?P[-.,\s]?U\b/gi, "SPPU")
      .replace(/\bD[-.,\s]?T[-.,\s]?E\b/gi, "DTE")
      .replace(/\bA[-.,\s]?I[-.,\s]?C[-.,\s]?T[-.,\s]?E\b/gi, "AICTE")
      .replace(/\bH[-.,\s]?O[-.,\s]?D\b/gi, "HOD")
      .replace(/\bT[-.,\s]?P[-.,\s]?O\b/gi, "TPO")
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

    // Trigger SPEAKING state on hardware LED immediately when speech playback starts
    setIsSpeaking(true);
    onStateChange('speaking');
    api.setLedState('SPEAKING');

    // Chromium keep-alive heartbeat: Prevents speech engine pause after fullstop
    speechHeartbeatRef.current = window.setInterval(() => {
      if (window.speechSynthesis.paused && !isCanceledRef.current) {
        window.speechSynthesis.resume();
      }
    }, 3000);

    const finishSpeech = () => {
      if (speechGenerationIdRef.current !== currentGen) return;
      clearAllVoiceTimers();
      activeUtterancesRef.current = [];
      (window as any).__buddy_active_utterance = null;
      setIsSpeaking(false);
      // Clean, smiling transition before returning to idle
      onStateChange('happy');
      api.setLedState('IDLE');
      transitionTimerRef.current = window.setTimeout(() => {
        if (speechGenerationIdRef.current === currentGen) {
          onStateChange('idle');
          transitionTimerRef.current = null;
        }
      }, 1500);
    };

    // Overall speech safety timer (prevents speech hanging indefinitely under any circumstance)
    const overallSafetyMs = Math.max(cleanText.length * 200, 15000) + 30000;
    speechWatchdogRef.current = window.setTimeout(() => {
      if (!isCanceledRef.current && speechGenerationIdRef.current === currentGen) {
        console.warn("[Browser Speech] Overall speech safety timer triggered, safely finishing.");
        finishSpeech();
      }
    }, overallSafetyMs);

    const speakChunk = (idx: number) => {
      if (isCanceledRef.current || speechGenerationIdRef.current !== currentGen || idx >= sentences.length) {
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
        if (!isCanceledRef.current && speechGenerationIdRef.current === currentGen) {
          currentIndex++;
          speakChunk(currentIndex);
        }
      }, chunkTimeoutMs);

      utterance.onend = () => {
        if (chunkWatchdogRef.current) {
          clearTimeout(chunkWatchdogRef.current);
          chunkWatchdogRef.current = null;
        }
        if (!isCanceledRef.current && speechGenerationIdRef.current === currentGen) {
          currentIndex++;
          speakChunk(currentIndex);
        }
      };

      utterance.onerror = (e) => {
        if (chunkWatchdogRef.current) {
          clearTimeout(chunkWatchdogRef.current);
          chunkWatchdogRef.current = null;
        }
        // Strictly prevent advancing if canceled or interrupted by user
        if (!isCanceledRef.current && speechGenerationIdRef.current === currentGen && e.error !== 'canceled' && e.error !== 'interrupted') {
          currentIndex++;
          speakChunk(currentIndex);
        }
      };

      window.speechSynthesis.speak(utterance);
    };

    setTimeout(() => {
      if (!isCanceledRef.current && speechGenerationIdRef.current === currentGen) {
        window.speechSynthesis.resume();
        speakChunk(0);
      }
    }, 50);
  }, [clearAllVoiceTimers, onStateChange]);

  const isEsp32RecordingRef = useRef(false);

  // Start Push-To-Talk Recording
  const startRecording = useCallback(async () => {
    // Stop any ongoing playback and immediately sync hardware and UI to 'listening'
    stopSpeaking('listening');

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
          // Automated graceful degradation: switch to laptop mic if robot mic is offline/unreachable
          if (result.error && result.error.includes('No audio received')) {
            onError("Robot mic offline. Switched to Laptop Mic.");
            setAudioInputSource('laptop');
          } else {
            onError(result.error || "No speech detected from robot microphone. Please speak clearly towards the robot's microphone.");
          }
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

    const genId = ++speechGenerationIdRef.current;
    isCanceledRef.current = false;
    clearAllVoiceTimers();

    activeUtterancesRef.current = [];
    (window as any).__buddy_active_utterance = null;
    if (currentAudioRef.current) {
      const a = currentAudioRef.current;
      a.onplay = null; a.onended = null; a.onerror = null; a.onloadedmetadata = null;
      try { a.pause(); a.currentTime = 0; a.src = ''; } catch {}
      currentAudioRef.current = null;
    }
    if ('speechSynthesis' in window) {
      try { window.speechSynthesis.cancel(); } catch {}
    }

    // Immediately enter SPEAKING state on UI face and hardware LED
    setIsSpeaking(true);
    onStateChange('speaking');
    api.setLedState('SPEAKING', 0.8);

    // Helper to play WAV/MP3 audio element
    const playAudioUrl = async (url: string) => {
      if (speechGenerationIdRef.current !== genId || isCanceledRef.current) return;
      const fullUrl = `http://${API_HOST}:8000${url}`;
      const outputTarget = (localStorage.getItem('buddy_audio_output_target') as 'robot' | 'laptop' | 'both') || 'both';
      console.log(`[Voice] Playing audio (${outputTarget} destination):`, fullUrl);
      const audio = new Audio(fullUrl);
      activeAudiosRef.current.add(audio);

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
        if (speechGenerationIdRef.current !== genId || isCanceledRef.current) return;
        const durationSec = (audio.duration && !isNaN(audio.duration) && isFinite(audio.duration) && audio.duration > 0)
          ? audio.duration
          : Math.max(text.length * 0.20, 8.0);
        // Generous buffer: actual duration + 25 seconds of grace period
        const safetyMs = (durationSec * 1000) + 25000;

        if (audioSafetyTimerRef.current) {
          clearTimeout(audioSafetyTimerRef.current);
        }
        audioSafetyTimerRef.current = window.setTimeout(() => {
          if (speechGenerationIdRef.current === genId && currentAudioRef.current === audio && !audio.paused && !audio.ended) {
            if (audio.duration && !isNaN(audio.duration) && audio.currentTime < (audio.duration - 0.75)) {
              armSafetyTimer();
              return;
            }
            console.warn("[Voice] Audio safety watchdog fired after full playback grace period.");
            currentAudioRef.current = null;
            setIsSpeaking(false);
            onStateChange('happy');
            api.setLedState('IDLE');
            transitionTimerRef.current = window.setTimeout(() => {
              if (speechGenerationIdRef.current === genId) {
                onStateChange('idle');
                transitionTimerRef.current = null;
              }
            }, 1500);
          }
        }, safetyMs);
      };

      audio.onloadedmetadata = () => {
        if (speechGenerationIdRef.current === genId && !isCanceledRef.current) {
          armSafetyTimer();
        }
      };

      // Audio playback start: Confirm and sustain SPEAKING state
      audio.onplay = () => {
        if (speechGenerationIdRef.current !== genId || isCanceledRef.current) {
          audio.pause();
          return;
        }
        setIsSpeaking(true);
        onStateChange('speaking');
        api.setLedState('SPEAKING', 0.8);
        armSafetyTimer();
      };

      // Audio playback completion: Transition hardware to IDLE with cheerful happy smile
      audio.onended = () => {
        activeAudiosRef.current.delete(audio);
        if (speechGenerationIdRef.current !== genId) return;
        clearAllVoiceTimers();
        setIsSpeaking(false);
        currentAudioRef.current = null;
        onStateChange('happy');
        api.setLedState('IDLE');
        transitionTimerRef.current = window.setTimeout(() => {
          if (speechGenerationIdRef.current === genId) {
            onStateChange('idle');
            transitionTimerRef.current = null;
          }
        }, 1500);
      };

      audio.onerror = (e) => {
        activeAudiosRef.current.delete(audio);
        if (speechGenerationIdRef.current !== genId || isCanceledRef.current) return;
        console.warn("[Voice] Audio element failed to play, switching to browser speech:", e);
        clearAllVoiceTimers();
        setIsSpeaking(false);
        onStateChange('idle');
        fallbackBrowserSpeech(text, genId);
      };

      try {
        await audio.play();
      } catch (err) {
        if (speechGenerationIdRef.current !== genId || isCanceledRef.current) return;
        console.warn("[Voice] audio.play() rejected (autoplay policy), switching to browser speech:", err);
        clearAllVoiceTimers();
        setIsSpeaking(false);
        onStateChange('idle');
        fallbackBrowserSpeech(text, genId);
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
      if (speechGenerationIdRef.current !== genId || isCanceledRef.current) {
        console.log("[Voice] Synthesis resolved after stop was clicked. Ignoring audio.");
        return;
      }
      if (synthRes && synthRes.audio_url) {
        console.log("[Voice] Neural audio ready:", synthRes.audio_url);
        await playAudioUrl(synthRes.audio_url);
      } else {
        fallbackBrowserSpeech(text, genId);
      }
    } catch (err) {
      if (speechGenerationIdRef.current !== genId || isCanceledRef.current) return;
      console.warn("Async synthesis request failed, using browser speech fallback:", err);
      fallbackBrowserSpeech(text, genId);
    }
  }, [isMuted, clearAllVoiceTimers, onStateChange, fallbackBrowserSpeech]);

  const playInstantAcknowledgment = useCallback(() => {
    // Disabled: Prevents premature SPEAKING LED overrides while AI orchestrator is thinking
  }, []);

  return {
    isRecording,
    isSpeaking,
    isMuted,
    toggleMute: () => {
      setIsMuted(prev => {
        const next = !prev;
        if (next) {
          stopSpeaking('idle');
        }
        return next;
      });
    },
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
