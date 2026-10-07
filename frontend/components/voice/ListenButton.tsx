'use client';

import React from 'react';
import { useVoiceAssistant } from '@/lib/voiceContext';
import { Volume2, Square } from 'lucide-react';

interface ListenButtonProps {
  text: string;
  id?: string;
  className?: string;
  size?: 'sm' | 'md';
}

export const ListenButton: React.FC<ListenButtonProps> = ({
  text,
  id = 'default',
  className = '',
  size = 'sm'
}) => {
  const {
    speak,
    stopSpeaking,
    state,
    currentlySpeakingId,
    setCurrentlySpeakingId
  } = useVoiceAssistant();

  const isCurrentPlaying = state === 'speaking' && currentlySpeakingId === id;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isCurrentPlaying) {
      stopSpeaking();
    } else {
      setCurrentlySpeakingId(id);
      speak(text, () => {
        setCurrentlySpeakingId(null);
      });
    }
  };

  const sizeClasses =
    size === 'sm'
      ? 'text-[11px] px-2.5 py-1 gap-1.5'
      : 'text-[12px] px-3.5 py-1.5 gap-2';

  return (
    <button
      onClick={handleClick}
      type="button"
      title={isCurrentPlaying ? 'Stop reading aloud' : 'Read explanation aloud'}
      className={`inline-flex items-center font-tech uppercase tracking-wider border rounded-none transition-all cursor-pointer ${
        isCurrentPlaying
          ? 'border-[#0c0c0c] bg-[#0c0c0c] text-[#ffffff]'
          : 'border-[#cecece] bg-[#ffffff] text-[#0c0c0c] hover:border-[#0c0c0c] hover:bg-[#fafafa]'
      } ${sizeClasses} ${className}`}
    >
      {isCurrentPlaying ? (
        <>
          <Square className="w-2.5 h-2.5 fill-current" />
          <span>Stop Audio</span>
        </>
      ) : (
        <>
          <Volume2 className="w-3.5 h-3.5" />
          <span>Listen</span>
        </>
      )}
    </button>
  );
};
