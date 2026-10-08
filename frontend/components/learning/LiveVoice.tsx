'use client';
import { useEffect, useRef, useState } from 'react';
import { Mic, MicOff, PhoneOff, Radio } from 'lucide-react';
import { LiveVoiceClient, type VoiceState } from '@/lib/liveVoice';

export function LiveVoice({ sessionId, onTranscript }: { sessionId: string; onTranscript: () => void }) {
  const [state, setState] = useState<VoiceState>('Idle');
  const [error, setError] = useState('');
  const [muted, setMuted] = useState(false);
  const client = useRef<LiveVoiceClient | null>(null);
  const transcript = useRef(onTranscript);
  useEffect(() => { transcript.current = onTranscript; }, [onTranscript]);
  useEffect(() => () => { client.current?.stop(); }, [sessionId]);
  const active = state !== 'Idle' && state !== 'Error';
  function start() {
    client.current?.stop(); setError(''); setMuted(false);
    client.current = new LiveVoiceClient({ state: setState, error: setError, transcript: () => transcript.current() });
    void client.current.start(sessionId);
  }
  return <section aria-label="Live voice teaching" style={{ border: '1px solid #34303f', borderRadius: 20, padding: 20, background: 'linear-gradient(135deg, #191224, #101010)' }}>
    <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', justifyContent: 'space-between' }}>
      <div><div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#d2bcff' }}><Radio size={18} /><strong>Talk with your tutor</strong></div>
        <p role="status" aria-live="polite" style={{ fontSize: 13, color: '#d0cbd9', margin: '8px 0' }}>{muted && active ? 'Microphone muted' : state} · Gemini Live</p></div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {!active ? <button onClick={start} style={buttonStyle}><Mic size={16} />{state === 'Error' ? 'Reconnect voice' : 'Start voice'}</button> : <>
          <button onClick={() => { client.current?.mute(!muted); setMuted(!muted); }} aria-pressed={muted} aria-label={muted ? 'Unmute microphone' : 'Mute microphone'} style={buttonStyle}>{muted ? <MicOff size={16} /> : <Mic size={16} />}{muted ? 'Unmute' : 'Mute'}</button>
          <button onClick={() => client.current?.stop()} style={buttonStyle}><PhoneOff size={16} />End</button>
        </>}
      </div>
    </div>
    <p style={{ fontSize: 12, lineHeight: 1.6, color: '#aaa3b4', marginBottom: 0 }}>Speak naturally and interrupt at any time. Microphone audio is sent to Gemini while connected; transcripts are saved to this session. Use headphones for clearer interruptions. Text chat remains available.</p>
    {error && <p role="alert" style={{ color: '#ffb4b4', fontSize: 13, marginTop: 12 }}>{error}</p>}
  </section>;
}
const buttonStyle = { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 7, minHeight: 44, padding: '10px 16px', borderRadius: 24, border: '1px solid #766092', background: '#392155', color: '#fff', cursor: 'pointer', fontSize: 13 };
export default LiveVoice;
