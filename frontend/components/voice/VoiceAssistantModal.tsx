'use client';

import React, { useState } from 'react';
import { useVoiceAssistant } from '@/lib/voiceContext';
import {
  Mic,
  MicOff,
  Volume2,
  Square,
  X,
  Send,
  Loader2,
  Sparkles,
  Keyboard,
  AlertTriangle
} from 'lucide-react';

export const VoiceAssistantModal: React.FC = () => {
  const {
    isOpen,
    state,
    transcript,
    interimTranscript,
    response,
    errorMessage,
    activeTopic,
    closeAssistant,
    startListening,
    stopListening,
    stopSpeaking,
    sendQuery,
    isSupported
  } = useVoiceAssistant();

  const [textInput, setTextInput] = useState('');
  const [showTextFallback, setShowTextFallback] = useState(false);

  if (!isOpen) return null;

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim()) return;
    const q = textInput.trim();
    setTextInput('');
    sendQuery(q);
  };

  const isListening = state === 'listening';
  const isSpeaking = state === 'speaking';
  const isProcessing = state === 'processing';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#000000]/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="w-full max-w-xl bg-[#ffffff] border border-[#0c0c0c] shadow-2xl p-6 md:p-8 flex flex-col justify-between min-h-[460px] relative transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Bar */}
        <div>
          <div className="flex items-center justify-between border-b border-[#cecece] pb-4 mb-6">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 border border-[#0c0c0c] rounded-full flex items-center justify-center">
                <span className="w-2.5 h-2.5 bg-[#0c0c0c] rounded-full animate-pulse" />
              </div>
              <div>
                <span className="font-tech text-[11px] uppercase tracking-widest text-[#6d6d6d] block">
                  AI VOICE TUTOR // ACTIVE SESSION
                </span>
                <h3 className="font-tech text-[16px] font-bold text-[#0c0c0c] uppercase truncate max-w-[340px]">
                  {activeTopic}
                </h3>
              </div>
            </div>

            <button
              onClick={closeAssistant}
              aria-label="Close Voice Assistant"
              className="p-1.5 border border-transparent hover:border-[#0c0c0c] transition-colors rounded-none"
            >
              <X className="w-5 h-5 text-[#0c0c0c]" />
            </button>
          </div>

          {/* Central Waveform & Interaction Orb */}
          <div className="flex flex-col items-center justify-center py-6 text-center">
            {/* Animated Audio Ring */}
            <div className="relative mb-6">
              <button
                onClick={isListening ? stopListening : startListening}
                disabled={isProcessing}
                className={`w-24 h-24 rounded-full border flex items-center justify-center transition-all duration-300 cursor-pointer ${
                  isListening
                    ? 'border-[#0c0c0c] bg-[#0c0c0c] text-[#ffffff] scale-110 shadow-lg'
                    : isSpeaking
                    ? 'border-[#0c0c0c] bg-[#f4f4f4] text-[#0c0c0c] animate-pulse'
                    : 'border-[#cecece] hover:border-[#0c0c0c] bg-[#ffffff] text-[#0c0c0c] hover:scale-105'
                }`}
                title={isListening ? 'Stop listening' : 'Start speaking'}
              >
                {isProcessing ? (
                  <Loader2 className="w-8 h-8 animate-spin" />
                ) : isSpeaking ? (
                  <Volume2 className="w-8 h-8" />
                ) : isListening ? (
                  <Mic className="w-8 h-8 animate-pulse text-red-500" />
                ) : (
                  <Mic className="w-8 h-8" />
                )}
              </button>

              {/* Pulsing ring indicator when listening */}
              {isListening && (
                <div className="absolute -inset-2 rounded-full border border-[#0c0c0c] animate-ping opacity-25 pointer-events-none" />
              )}
            </div>

            {/* State Prompt */}
            <div className="font-tech text-[13px] tracking-wider uppercase text-[#6d6d6d] mb-2">
              {isListening
                ? 'Listening to your question...'
                : isProcessing
                ? 'Analyzing with First-Principles...'
                : isSpeaking
                ? 'Learnova is speaking explanation'
                : 'Tap microphone to speak'}
            </div>

            {/* Live Student Speech Transcription */}
            {(transcript || interimTranscript) && (
              <div className="w-full mt-2 p-3 bg-[#fafafa] border border-[#cecece] text-left">
                <span className="font-tech text-[10px] tracking-widest text-[#6d6d6d] uppercase block mb-1">
                  You Said:
                </span>
                <p className="font-sans text-[15px] text-[#0c0c0c]">
                  {transcript}
                  {interimTranscript && (
                    <span className="text-[#6d6d6d] italic"> {interimTranscript}...</span>
                  )}
                </p>
              </div>
            )}

            {/* AI Voice Response Output */}
            {response && (
              <div className="w-full mt-4 p-4 bg-[#ffffff] border border-[#0c0c0c] text-left max-h-[160px] overflow-y-auto">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-tech text-[10px] tracking-widest text-[#0c0c0c] uppercase font-bold flex items-center gap-1.5">
                    <Sparkles className="w-3 h-3 text-[#0c0c0c]" />
                    Learnova Tutor Response:
                  </span>
                  {isSpeaking && (
                    <button
                      onClick={stopSpeaking}
                      className="inline-flex items-center gap-1 px-2 py-0.5 border border-[#0c0c0c] text-[11px] font-tech uppercase hover:bg-[#0c0c0c] hover:text-[#ffffff] transition-colors"
                    >
                      <Square className="w-2 h-2 fill-current" /> Stop Audio
                    </button>
                  )}
                </div>
                <p className="font-sans text-[14px] text-[#0c0c0c] leading-relaxed">
                  {response}
                </p>
              </div>
            )}

            {/* Error Message */}
            {errorMessage && (
              <div className="w-full mt-3 p-3 bg-[#fce8e6] border border-[#f5b4af] text-[#c5221f] text-[12px] font-tech uppercase flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}
          </div>
        </div>

        {/* Footer Controls & Text Fallback */}
        <div className="border-t border-[#cecece] pt-4 mt-2">
          {showTextFallback ? (
            <form onSubmit={handleTextSubmit} className="flex gap-2">
              <input
                type="text"
                placeholder="Type your question for Learnova..."
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                autoFocus
                className="flex-1 border-b border-[#0c0c0c] bg-transparent py-1.5 px-0 text-[14px] outline-none font-sans"
              />
              <button
                type="submit"
                disabled={!textInput.trim() || isProcessing}
                className="px-4 py-1.5 bg-[#0c0c0c] text-[#ffffff] font-tech text-[12px] uppercase disabled:opacity-40"
              >
                Send
              </button>
              <button
                type="button"
                onClick={() => setShowTextFallback(false)}
                className="px-2 py-1.5 border border-[#cecece] text-[#6d6d6d] font-tech text-[12px] uppercase hover:border-[#0c0c0c]"
              >
                Cancel
              </button>
            </form>
          ) : (
            <div className="flex items-center justify-between text-[12px] font-tech text-[#6d6d6d]">
              <button
                onClick={() => setShowTextFallback(true)}
                className="inline-flex items-center gap-1.5 uppercase hover:text-[#0c0c0c] transition-colors cursor-pointer"
              >
                <Keyboard className="w-3.5 h-3.5" />
                <span>Ask by text instead</span>
              </button>

              <div className="flex items-center gap-3">
                {isListening ? (
                  <button
                    onClick={stopListening}
                    className="uppercase text-[#c5221f] font-bold underline cursor-pointer"
                  >
                    Done Speaking
                  </button>
                ) : (
                  <button
                    onClick={startListening}
                    disabled={isProcessing}
                    className="uppercase text-[#0c0c0c] font-bold underline cursor-pointer"
                  >
                    Tap to Speak
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
