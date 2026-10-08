export type VoiceState = 'Idle' | 'Connecting' | 'Listening' | 'Thinking' | 'Speaking' | 'Interrupted' | 'Error';
type Callbacks = { state: (s: VoiceState) => void; error: (s: string) => void; transcript: () => void };

/** PCM transport owns its devices and releases them on every close/error path. */
export class LiveVoiceClient {
  private socket?: WebSocket;
  private context?: AudioContext;
  private stream?: MediaStream;
  private processor?: ScriptProcessorNode;
  private source?: MediaStreamAudioSourceNode;
  private silent?: GainNode;
  private playing = new Set<AudioBufferSourceNode>();
  private nextTime = 0;
  private stopped = false;
  private muted = false;
  private blocked = false;
  private speakingFrames = 0;
  private ready = false;
  private connectTimer?: ReturnType<typeof setTimeout>;
  constructor(private callbacks: Callbacks) {}

  async start(sessionId: string) {
    try {
      this.callbacks.state('Connecting');
      if (!navigator.mediaDevices?.getUserMedia) throw new Error('Microphone access requires HTTPS or localhost and a supported browser.');
      // Construct and resume during the user's click to support mobile autoplay policies.
      this.context = new AudioContext();
      await this.context.resume();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }, video: false });
      if (this.stopped) { stream.getTracks().forEach(t => t.stop()); return; }
      this.stream = stream;
      const base = process.env.NEXT_PUBLIC_VOICE_URL || process.env.NEXT_PUBLIC_API_URL || window.location.origin;
      const url = new URL(`/api/v2/sessions/${encodeURIComponent(sessionId)}/voice`, base);
      url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
      this.socket = new WebSocket(url);
      this.connectTimer = setTimeout(() => this.fail('Voice connection timed out. Try again or continue using text.'), 20000);
      this.socket.onmessage = event => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'ready') {
            clearTimeout(this.connectTimer); this.ready = true; this.capture(); this.callbacks.state('Listening');
          } else if (message.type === 'audio' && !this.blocked) this.play(message.data);
          else if (message.type === 'interrupted') { this.clearAudio(); this.blocked = false; this.callbacks.state('Interrupted'); }
          else if (message.type === 'turn_complete') { this.blocked = false; if (!this.playing.size) this.callbacks.state('Listening'); this.callbacks.transcript(); }
          else if (message.type === 'thinking') this.callbacks.state('Thinking');
          else if (message.type === 'error') this.fail(message.message || 'Voice is unavailable. Continue using text.');
        } catch { this.fail('The voice connection returned an invalid response. Please reconnect.'); }
      };
      this.socket.onerror = () => this.fail('Voice connection failed. Check your connection and sign-in, then reconnect. Text remains available.');
      this.socket.onclose = () => { if (!this.stopped) this.fail('Voice disconnected. Reconnect to continue; your saved conversation is preserved.'); };
    } catch (error) { this.fail(error instanceof Error ? error.message : 'Microphone access failed.'); }
  }

  private send(value: object) { if (this.socket?.readyState === WebSocket.OPEN) this.socket.send(JSON.stringify(value)); }
  private capture() {
    const context = this.context!;
    this.source = context.createMediaStreamSource(this.stream!);
    // ScriptProcessor is the compatibility path; small frames keep local interruption responsive.
    this.processor = context.createScriptProcessor(2048, 1, 1);
    this.silent = context.createGain(); this.silent.gain.value = 0;
    this.processor.onaudioprocess = event => {
      if (this.stopped || this.muted || !this.ready) return;
      if ((this.socket?.bufferedAmount || 0) > 128000) { this.fail('Connection too slow for live audio. Reconnect or use text.'); return; }
      const input = event.inputBuffer.getChannelData(0);
      let energy = 0; for (const sample of input) energy += sample * sample;
      this.speakingFrames = Math.sqrt(energy / input.length) > 0.035 ? this.speakingFrames + 1 : 0;
      if (this.speakingFrames >= 2 && this.playing.size && !this.blocked) {
        this.blocked = true; this.clearAudio(); this.send({ type: 'interrupt' }); this.callbacks.state('Interrupted');
      }
      const ratio = context.sampleRate / 16000;
      const pcm = new DataView(new ArrayBuffer(Math.floor(input.length / ratio) * 2));
      for (let i = 0; i < pcm.byteLength / 2; i++) {
        const start = Math.floor(i * ratio), end = Math.min(input.length, Math.max(start + 1, Math.floor((i + 1) * ratio)));
        let sum = 0; for (let j = start; j < end; j++) sum += input[j];
        const sample = Math.max(-1, Math.min(1, sum / (end - start)));
        pcm.setInt16(i * 2, sample < 0 ? sample * 32768 : sample * 32767, true);
      }
      let binary = ''; for (const byte of new Uint8Array(pcm.buffer)) binary += String.fromCharCode(byte);
      this.send({ type: 'audio', data: btoa(binary) });
    };
    this.source.connect(this.processor); this.processor.connect(this.silent); this.silent.connect(context.destination);
  }
  private play(encoded: string) {
    const context = this.context!;
    if (this.nextTime - context.currentTime > 30) { this.fail('Voice playback fell behind. Reconnect to resume or continue with text.'); return; }
    const bytes = Uint8Array.from(atob(encoded), c => c.charCodeAt(0));
    const view = new DataView(bytes.buffer);
    const buffer = context.createBuffer(1, bytes.length / 2, 24000);
    const channel = buffer.getChannelData(0);
    for (let i = 0; i < channel.length; i++) channel[i] = view.getInt16(i * 2, true) / 32768;
    const source = context.createBufferSource(); source.buffer = buffer; source.connect(context.destination);
    this.nextTime = Math.max(context.currentTime + 0.015, this.nextTime);
    source.start(this.nextTime); this.nextTime += buffer.duration; this.playing.add(source);
    source.onended = () => { this.playing.delete(source); source.disconnect(); if (!this.playing.size && !this.stopped && !this.blocked) this.callbacks.state('Listening'); };
    this.callbacks.state('Speaking');
  }
  private clearAudio() { for (const source of this.playing) { source.onended = null; try { source.stop(); } catch {} source.disconnect(); } this.playing.clear(); this.nextTime = 0; }
  mute(value: boolean) { this.muted = value; this.stream?.getAudioTracks().forEach(t => { t.enabled = !value; }); if (value) this.send({ type: 'pause' }); }
  private fail(message: string) { if (this.stopped) return; this.stop(); this.callbacks.error(message); this.callbacks.state('Error'); }
  stop() {
    this.stopped = true; this.ready = false; clearTimeout(this.connectTimer); this.clearAudio();
    this.socket?.close(); if (this.processor) { this.processor.onaudioprocess = null; this.processor.disconnect(); }
    this.source?.disconnect(); this.silent?.disconnect(); this.stream?.getTracks().forEach(t => t.stop());
    void this.context?.close(); this.callbacks.state('Idle');
  }
}
