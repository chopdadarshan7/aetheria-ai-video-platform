/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useStore, VoiceProfile } from '../store';
import { 
  ArrowLeft, Plus, Trash2, Volume2, Music, Sparkles, Mic,
  Play, Download, RefreshCw, CheckCircle2, AlertCircle, PlayCircle
} from 'lucide-react';
import Link from 'next/link';

export default function AudioStudio() {
  const router = useRouter();
  const {
    token, voices, audioJobs, loading,
    fetchVoices, createVoice, deleteVoice, triggerAudioJob
  } = useStore();

  const [voiceName, setVoiceName] = useState('');
  const [voiceLang, setVoiceLang] = useState('en');

  // TTS states
  const [ttsText, setTtsText] = useState('');
  const [selectedVoiceId, setSelectedVoiceId] = useState('');

  // Music states
  const [musicPrompt, setMusicPrompt] = useState('');
  const [musicDuration, setMusicDuration] = useState(10);

  useEffect(() => {
    if (!token) {
      router.push('/');
    } else {
      fetchVoices();
    }
  }, [token]);

  const handleCreateVoice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!voiceName) return;
    try {
      await createVoice(voiceName, voiceLang);
      setVoiceName('');
    } catch (err) {
      console.error(err);
    }
  };

  const handleTriggerTTS = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ttsText) return;
    try {
      await triggerAudioJob({
        job_type: 'tts',
        prompt: ttsText,
        voice_profile_id: selectedVoiceId ? parseInt(selectedVoiceId) : undefined
      });
      setTtsText('');
    } catch (err) {
      console.error(err);
    }
  };

  const handleTriggerMusic = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!musicPrompt) return;
    try {
      await triggerAudioJob({
        job_type: 'music',
        prompt: musicPrompt
      });
      setMusicPrompt('');
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex-1 min-h-screen bg-background text-white p-6 relative">
      <div className="absolute top-10 left-1/4 glowing-orb bg-primary/10" />

      {/* HEADER NAVBAR */}
      <div className="flex items-center justify-between mb-8 relative z-10 border-b border-white/5 pb-4">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="p-2 hover:bg-white/5 rounded-lg border border-white/5 text-zinc-300 transition">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-wide flex items-center gap-2">
              <Volume2 className="w-5 h-5 text-primary" />
              Audio Intelligence Studio
            </h1>
            <p className="text-xs text-zinc-400">Clone voices, generate custom narrations, and build cinematic soundscapes.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 relative z-10">
        
        {/* VOICE PROFILES SIDEBAR */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="glass-panel p-5 rounded-xl border border-white/5 bg-black/40">
            <h2 className="text-sm font-bold text-zinc-300 mb-4 uppercase tracking-wider flex items-center gap-1.5">
              <Mic className="w-4 h-4 text-primary" /> Create Voice Profile
            </h2>
            <form onSubmit={handleCreateVoice} className="space-y-4">
              <div>
                <label className="text-[10px] text-zinc-400 block mb-1">Speaker Name</label>
                <input
                  type="text"
                  required
                  value={voiceName}
                  onChange={(e) => setVoiceName(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
                  placeholder="e.g. Cinematic Narrator Male"
                />
              </div>
              <div>
                <label className="text-[10px] text-zinc-400 block mb-1">Target Language</label>
                <select
                  value={voiceLang}
                  onChange={(e) => setVoiceLang(e.target.value)}
                  className="w-full bg-zinc-900 border border-white/10 text-xs text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none"
                >
                  <option value="en">English (US/UK)</option>
                  <option value="es">Spanish (Español)</option>
                  <option value="fr">French (Français)</option>
                  <option value="de">German (Deutsch)</option>
                </select>
              </div>
              <button
                type="submit"
                className="w-full py-2 bg-white/5 border border-white/10 hover:border-white/20 text-white font-semibold text-xs rounded-lg flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                Initialize voice profile
              </button>
            </form>
          </div>

          <div className="glass-panel p-5 rounded-xl border border-white/5 bg-black/40">
            <h2 className="text-sm font-bold text-zinc-300 mb-3 uppercase tracking-wider">Voice Library</h2>
            {voices.length === 0 ? (
              <span className="text-xs text-zinc-500">No custom profiles added.</span>
            ) : (
              <div className="flex flex-col gap-2">
                {voices.map(voice => (
                  <div 
                    key={voice.id}
                    className="p-3 rounded-lg border border-white/5 bg-white/5 flex justify-between items-center text-zinc-300"
                  >
                    <div className="flex flex-col min-w-0">
                      <span className="text-xs font-semibold truncate">{voice.name}</span>
                      <span className="text-[9px] text-zinc-500 mt-0.5 uppercase">Lang: {voice.language}</span>
                    </div>
                    <button
                      onClick={() => deleteVoice(voice.id)}
                      className="p-1 hover:text-red-400 text-zinc-500 rounded"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* WORKSPACE & RENDER JOBS */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* TEXT TO SPEECH (TTS) */}
            <div className="glass-panel p-5 rounded-xl border border-white/5 bg-black/40 flex flex-col gap-4">
              <h2 className="text-sm font-bold text-zinc-200 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-primary" /> Text-to-Speech Script
              </h2>
              <form onSubmit={handleTriggerTTS} className="space-y-4 flex-1 flex flex-col justify-between">
                <div className="space-y-3">
                  <div>
                    <label className="text-[10px] text-zinc-400 block mb-1">Speaker Embedding Profile</label>
                    <select
                      value={selectedVoiceId}
                      onChange={(e) => setSelectedVoiceId(e.target.value)}
                      className="w-full bg-zinc-900 border border-white/10 text-xs text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none"
                    >
                      <option value="">-- Select voice preset --</option>
                      {voices.map(v => (
                        <option key={v.id} value={v.id}>{v.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] text-zinc-400 block mb-1">Narration Script Prompt</label>
                    <textarea
                      required
                      value={ttsText}
                      onChange={(e) => setTtsText(e.target.value)}
                      className="w-full p-2.5 rounded-lg glass-input text-xs resize-none"
                      rows={3}
                      placeholder="Welcome to Aetheria. Enter any speech script here..."
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  className="w-full py-2 bg-primary hover:bg-primary-hover font-semibold text-xs rounded-lg flex items-center justify-center gap-1.5 cursor-pointer glow-btn mt-4"
                >
                  <Play className="w-3 h-3 fill-white" />
                  Generate speech track
                </button>
              </form>
            </div>

            {/* BACKGROUND MUSIC */}
            <div className="glass-panel p-5 rounded-xl border border-white/5 bg-black/40 flex flex-col gap-4">
              <h2 className="text-sm font-bold text-zinc-200 uppercase tracking-wider flex items-center gap-1.5">
                <Music className="w-4 h-4 text-secondary" /> AI Music Generator
              </h2>
              <form onSubmit={handleTriggerMusic} className="space-y-4 flex-1 flex flex-col justify-between">
                <div className="space-y-3">
                  <div>
                    <label className="text-[10px] text-zinc-400 block mb-1">Track duration (seconds)</label>
                    <select
                      value={musicDuration}
                      onChange={(e) => setMusicDuration(parseInt(e.target.value))}
                      className="w-full bg-zinc-900 border border-white/10 text-xs text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none"
                    >
                      <option value={10}>10 seconds</option>
                      <option value={20}>20 seconds</option>
                      <option value={30}>30 seconds</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] text-zinc-400 block mb-1">Background Music Prompt</label>
                    <textarea
                      required
                      value={musicPrompt}
                      onChange={(e) => setMusicPrompt(e.target.value)}
                      className="w-full p-2.5 rounded-lg glass-input text-xs resize-none"
                      rows={3}
                      placeholder="e.g. Retro synthesizer beat, upbeat synthwave loop..."
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  className="w-full py-2 bg-white/5 border border-white/10 hover:border-white/20 text-white font-semibold text-xs rounded-lg flex items-center justify-center gap-1.5 cursor-pointer mt-4"
                >
                  <Sparkles className="w-3.5 h-3.5 text-secondary" />
                  Compile background track
                </button>
              </form>
            </div>

          </div>

          {/* AUDIO RENDER LIST */}
          <div className="glass-panel p-5 rounded-xl border border-white/5 bg-black/40">
            <h2 className="text-sm font-bold text-zinc-300 mb-4 uppercase tracking-wider">Audio Workspace Queue</h2>
            {audioJobs.length === 0 ? (
              <span className="text-xs text-zinc-500">Audio rendering queue is currently empty.</span>
            ) : (
              <div className="flex flex-col gap-3">
                {audioJobs.map(job => (
                  <div 
                    key={job.id} 
                    className="p-3.5 rounded-lg bg-white/5 border border-white/5 flex flex-col gap-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold capitalize text-zinc-300">{job.job_type} render job #{job.id}</span>
                      <div className="flex items-center gap-2">
                        {job.status === 'RUNNING' && (
                          <span className="flex items-center gap-1 text-[10px] text-blue-400 bg-blue-950/40 border border-blue-500/25 px-2 py-0.5 rounded-full">
                            <RefreshCw className="w-3 h-3 animate-spin" /> Processing {job.progress}%
                          </span>
                        )}
                        {job.status === 'SUCCESS' && (
                          <span className="flex items-center gap-1 text-[10px] text-green-400 bg-green-950/40 border border-green-500/25 px-2 py-0.5 rounded-full">
                            <CheckCircle2 className="w-3 h-3" /> Cloned
                          </span>
                        )}
                        {job.status === 'FAILED' && (
                          <span className="flex items-center gap-1 text-[10px] text-red-400 bg-red-950/40 border border-red-500/25 px-2 py-0.5 rounded-full">
                            <AlertCircle className="w-3 h-3" /> FAILED
                          </span>
                        )}
                      </div>
                    </div>

                    {job.prompt && (
                      <p className="text-[10px] text-zinc-400 italic bg-black/25 p-2 rounded border border-white/5">
                        &ldquo;{job.prompt}&rdquo;
                      </p>
                    )}

                    {job.status === 'SUCCESS' && job.result_url && (
                      <div className="flex items-center gap-3 mt-1.5 p-1 bg-black/40 rounded border border-white/5">
                        <audio src={job.result_url} controls className="w-full max-w-md h-8 outline-none" />
                        <a 
                          href={job.result_url} 
                          download 
                          className="p-1.5 bg-zinc-800 text-zinc-300 hover:text-white rounded transition"
                          title="Download Audio"
                        >
                          <Download className="w-3.5 h-3.5" />
                        </a>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
