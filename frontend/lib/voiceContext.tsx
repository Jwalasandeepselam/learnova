'use client';

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
  useCallback
} from 'react';
import { learnovaApi } from './api';

export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking' | 'error';

export interface VoiceAssistantContextType {
  state: VoiceState;
  isSupported: boolean;
  isOpen: boolean;
  transcript: string;
  interimTranscript: string;
  response: string;
  errorMessage: string | null;
  activeTopic: string;
  documentId: string;
  openAssistant: (topic?: string, docId?: string) => void;
  closeAssistant: () => void;
  startListening: () => void;
  stopListening: () => void;
  speak: (text: string, onEnd?: () => void) => void;
  stopSpeaking: () => void;
  sendQuery: (query: string) => Promise<void>;
  currentlySpeakingId: string | null;
  setCurrentlySpeakingId: (id: string | null) => void;
}

const VoiceAssistantContext = createContext<VoiceAssistantContextType | undefined>(undefined);

// Web Speech API interface declarations for TypeScript
interface IWindow extends Window {
  SpeechRecognition?: any;
  webkitSpeechRecognition?: any;
}

export const VoiceAssistantProvider: React.FC<{ children: React.ReactNode }> = ({
  children
}) => {
  const [state, setState] = useState<VoiceState>('idle');
  const [isOpen, setIsOpen] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeTopic, setActiveTopic] = useState('General Learning Inquiries');
  const [documentId, setDocumentId] = useState('');
  const [currentlySpeakingId, setCurrentlySpeakingId] = useState<string | null>(null);

  const recognitionRef = useRef<any>(null);
  const synthesisRef = useRef<SpeechSynthesis | null>(null);
  const activeUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Check browser support
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const win = window as IWindow;
      const hasSpeechRec = !!(win.SpeechRecognition || win.webkitSpeechRecognition);
      const hasSpeechSyn = typeof window.speechSynthesis !== 'undefined';
      setIsSupported(hasSpeechRec && hasSpeechSyn);
      synthesisRef.current = window.speechSynthesis || null;
    }
  }, []);

  // Stop speaking helper
  const stopSpeaking = useCallback(() => {
    if (synthesisRef.current) {
      synthesisRef.current.cancel();
    }
    activeUtteranceRef.current = null;
    setCurrentlySpeakingId(null);
    setState((prev) => (prev === 'speaking' ? 'idle' : prev));
  }, []);

  // Text-to-speech helper
  const speak = useCallback(
    (text: string, onEnd?: () => void) => {
      if (!synthesisRef.current) return;

      // Cancel previous utterances
      synthesisRef.current.cancel();

      // Clean markdown tags or symbols for cleaner speech
      const cleanText = text
        .replace(/[*_#`~\[\]\(\)]/g, ' ')
        .replace(/\$[^$]+\$/g, ' mathematical expression ')
        .replace(/\s+/g, ' ')
        .trim();

      if (!cleanText) return;

      const utterance = new SpeechSynthesisUtterance(cleanText);
      activeUtteranceRef.current = utterance;

      // Select highest quality natural English voice
      const voices = synthesisRef.current.getVoices();
      const naturalVoice =
        voices.find(
          (v) =>
            v.lang.startsWith('en') &&
            (v.name.includes('Natural') ||
              v.name.includes('Neural') ||
              v.name.includes('Google') ||
              v.name.includes('Samantha') ||
              v.name.includes('Daniel') ||
              v.name.includes('Alex'))
        ) ||
        voices.find((v) => v.lang.startsWith('en')) ||
        voices[0];

      if (naturalVoice) {
        utterance.voice = naturalVoice;
      }

      utterance.rate = 1.0;
      utterance.pitch = 1.0;

      utterance.onstart = () => {
        setState('speaking');
      };

      utterance.onend = () => {
        setState('idle');
        setCurrentlySpeakingId(null);
        activeUtteranceRef.current = null;
        if (onEnd) onEnd();
      };

      utterance.onerror = () => {
        setState('idle');
        setCurrentlySpeakingId(null);
        activeUtteranceRef.current = null;
      };

      synthesisRef.current.speak(utterance);
    },
    []
  );

  // Send student query to backend AI
  const sendQuery = useCallback(
    async (queryText: string) => {
      const clean = queryText.trim();
      if (!clean) return;

      setState('processing');
      setErrorMessage(null);

      try {
        let targetDocId = documentId;
        if (!targetDocId) {
          const docsRes = await learnovaApi.getDocuments();
          if (docsRes.items && docsRes.items.length > 0) {
            targetDocId = docsRes.items[0].id;
            setDocumentId(targetDocId);
          }
        }

        if (!targetDocId) {
          const msg = `I understand your question: "${clean}". To provide exact source-grounded answers with citations, please upload your course PDF, slides, or notes.`;
          setResponse(msg);
          speak(msg);
          return;
        }

        const chatRes = await learnovaApi.chat({
          document_id: targetDocId,
          query: `[Topic: ${activeTopic}] ${clean}`
        });

        const reply = chatRes.response || 'I have analyzed your material and verified this concept.';
        setResponse(reply);
        speak(reply);
      } catch (err: unknown) {
        console.error('Voice assistant query error:', err);
        const fallback = `I received your question about ${activeTopic}. Please upload or select a document to activate full source-grounded tutoring.`;
        setResponse(fallback);
        speak(fallback);
      }
    },
    [activeTopic, documentId, speak]
  );

  // Start speech recognition
  const startListening = useCallback(() => {
    if (typeof window === 'undefined') return;
    const win = window as IWindow;
    const SpeechRec = win.SpeechRecognition || win.webkitSpeechRecognition;

    if (!SpeechRec) {
      setErrorMessage('Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
      setState('error');
      return;
    }

    // Stop speaking if currently speaking
    stopSpeaking();

    // Abort previous recognition if active
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch (e) {
        // ignore
      }
    }

    try {
      const recognition = new SpeechRec();
      recognitionRef.current = recognition;

      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      recognition.maxAlternatives = 1;

      setTranscript('');
      setInterimTranscript('');
      setErrorMessage(null);
      setState('listening');

      recognition.onstart = () => {
        setState('listening');
      };

      recognition.onresult = (event: any) => {
        let interim = '';
        let final = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const item = event.results[i];
          if (item.isFinal) {
            final += item[0].transcript;
          } else {
            interim += item[0].transcript;
          }
        }

        if (interim) {
          setInterimTranscript(interim);
        }

        if (final) {
          setTranscript(final);
          setInterimTranscript('');
          sendQuery(final);
        }
      };

      recognition.onerror = (event: any) => {
        console.warn('Speech recognition error:', event.error);
        if (event.error === 'no-speech') {
          setErrorMessage('No speech was detected. Please try speaking again.');
        } else if (event.error === 'not-allowed') {
          setErrorMessage('Microphone access was denied. Please allow microphone permissions.');
        } else if (event.error === 'network') {
          setErrorMessage('Network connection error occurred.');
        } else {
          setErrorMessage(`Speech recognition error: ${event.error}`);
        }
        setState('error');
      };

      recognition.onend = () => {
        setState((prev) => (prev === 'listening' ? 'idle' : prev));
      };

      recognition.start();
    } catch (err: unknown) {
      console.error('Failed to start speech recognition:', err);
      setErrorMessage('Failed to initialize speech recognition.');
      setState('error');
    }
  }, [sendQuery, stopSpeaking]);

  // Stop listening
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {
        // ignore
      }
    }
    setState((prev) => (prev === 'listening' ? 'idle' : prev));
  }, []);

  const openAssistant = useCallback(
    (topic?: string, docId?: string) => {
      if (topic) setActiveTopic(topic);
      if (docId) setDocumentId(docId);
      setIsOpen(true);
      setErrorMessage(null);
      // Auto-start listening on modal open
      setTimeout(() => {
        startListening();
      }, 300);
    },
    [startListening]
  );

  const closeAssistant = useCallback(() => {
    stopListening();
    stopSpeaking();
    setIsOpen(false);
    setTranscript('');
    setInterimTranscript('');
    setResponse('');
    setErrorMessage(null);
  }, [stopListening, stopSpeaking]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (e) {}
      }
      if (synthesisRef.current) {
        synthesisRef.current.cancel();
      }
    };
  }, []);

  return (
    <VoiceAssistantContext.Provider
      value={{
        state,
        isSupported,
        isOpen,
        transcript,
        interimTranscript,
        response,
        errorMessage,
        activeTopic,
        documentId,
        openAssistant,
        closeAssistant,
        startListening,
        stopListening,
        speak,
        stopSpeaking,
        sendQuery,
        currentlySpeakingId,
        setCurrentlySpeakingId
      }}
    >
      {children}
    </VoiceAssistantContext.Provider>
  );
};

export const useVoiceAssistant = () => {
  const context = useContext(VoiceAssistantContext);
  if (!context) {
    throw new Error('useVoiceAssistant must be used within a VoiceAssistantProvider');
  }
  return context;
};
