'use client';

import React from 'react';
import { useVoiceAssistant } from '@/lib/voiceContext';
import { Mic, Volume2, Square, Loader2, AlertCircle } from 'lucide-react';

export const FloatingVoiceButton: React.FC = () => {
  const {
    state,
    isOpen,
    openAssistant,
    closeAssistant,
    stopSpeaking,
    startListening
  } = useVoiceAssistant();

  // If modal is open, we can hide or dim the floating button
  if (isOpen) return null;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (state === 'speaking') {
      stopSpeaking();
    } else if (state === 'error') {
      startListening();
    } else {
      openAssistant();
    }
  };

  const renderContent = () => {
    switch (state) {
      case 'listening':
        return (
          <>
            <span className="relative flex h-3.5 w-3.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-red-600"></span>
            </span>
            <span className="font-tech tracking-wider text-[14px] sm:text-[15px] uppercase font-bold text-red-600">
              🔴 I'm listening...
            </span>
            <div className="flex items-center gap-1 ml-1">
              <span className="w-1 h-3.5 bg-red-600 animate-pulse"></span>
              <span className="w-1 h-5 bg-red-600 animate-pulse delay-75"></span>
              <span className="w-1 h-2.5 bg-red-600 animate-pulse delay-150"></span>
            </div>
          </>
        );

      case 'processing':
        return (
          <>
            <Loader2 className="w-4 h-4 animate-spin text-[#0c0c0c]" />
            <span className="font-tech tracking-wider text-[14px] sm:text-[15px] uppercase font-medium">
              ◌ Thinking...
            </span>
          </>
        );

      case 'speaking':
        return (
          <>
            <Volume2 className="w-4 h-4 text-[#0c0c0c] animate-bounce" />
            <span className="font-tech tracking-wider text-[14px] sm:text-[15px] uppercase font-medium">
              🔊 Learnova is speaking...
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                stopSpeaking();
              }}
              title="Stop playback"
              className="ml-2 px-2 py-1 border border-[#0c0c0c] rounded-full hover:bg-[#0c0c0c] hover:text-[#ffffff] transition-colors flex items-center gap-1 text-[11px] font-tech uppercase"
            >
              <Square className="w-2.5 h-2.5 fill-current" />
              <span>Stop</span>
            </button>
          </>
        );

      case 'error':
        return (
          <>
            <AlertCircle className="w-4 h-4 text-amber-600" />
            <span className="font-tech tracking-wider text-[14px] sm:text-[15px] uppercase font-medium text-amber-700">
              ⚠ Try again
            </span>
          </>
        );

      case 'idle':
      default:
        return (
          <>
            <div className="w-8 h-8 rounded-full bg-[#ffffff] text-[#0c0c0c] flex items-center justify-center transition-transform group-hover:scale-110">
              <Mic className="w-4 h-4" />
            </div>
            <span className="font-tech tracking-wider text-[14px] sm:text-[15px] uppercase font-bold">
              Talk to Learnova
            </span>
          </>
        );
    }
  };

  const isIdle = state === 'idle';

  return (
    <div className="fixed bottom-6 right-6 z-50 select-none pb-[max(1.5rem,env(safe-area-inset-bottom))] pr-[max(1.5rem,env(safe-area-inset-right))]">
      <button
        onClick={handleClick}
        aria-label="Talk to Learnova AI Voice Assistant"
        className={`group flex items-center gap-3 px-6 sm:px-8 py-3.5 min-h-[64px] sm:min-h-[76px] rounded-full border transition-all duration-300 shadow-2xl cursor-pointer hover:scale-[1.04] active:scale-[0.98] ${
          isIdle
            ? 'bg-[#0c0c0c] text-[#ffffff] border-[#0c0c0c] hover:bg-[#000000]'
            : 'bg-[#ffffff] text-[#0c0c0c] border-[#0c0c0c] ring-2 ring-[#0c0c0c]/10'
        }`}
      >
        {renderContent()}
      </button>
    </div>
  );
};
