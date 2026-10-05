import React, { useEffect, useRef } from 'react';

interface AudioEngineProps {
  audioUrl: string | null;
  isMuted: boolean;
  onAudioEnded: () => void;
  onAudioStarted: () => void;
}

export const AudioEngine: React.FC<AudioEngineProps> = ({
  audioUrl,
  isMuted,
  onAudioEnded,
  onAudioStarted,
}) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (!audioUrl || isMuted) return;

    if (!audioRef.current) {
      audioRef.current = new Audio();
    }

    const audio = audioRef.current;
    audio.src = audioUrl;
    audio.volume = isMuted ? 0.0 : 1.0;

    const handlePlay = () => {
      onAudioStarted();
    };

    const handleEnded = () => {
      onAudioEnded();
    };

    const handleError = (e: Event) => {
      console.warn('[AudioEngine]: Audio playback error or interrupted', e);
      onAudioEnded();
    };

    audio.addEventListener('play', handlePlay);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);

    audio.play().catch((err) => {
      console.warn('[AudioEngine]: Browser autoplay policy or playback error', err);
      onAudioEnded();
    });

    return () => {
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
    };
  }, [audioUrl, isMuted]);

  return null;
};
