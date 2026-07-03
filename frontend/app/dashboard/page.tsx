/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import React, { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useStore, RenderJob } from '../store';
import { 
  Sparkles, Film, Image as ImageIcon, Video, UserCheck, 
  CreditCard, Activity, LogOut, Download, 
  RefreshCw, Play, Plus, UploadCloud, CheckCircle2, 
  AlertCircle, Cpu, Sliders, Settings, HelpCircle, 
  RefreshCw as ResetIcon, Trash2, Eye, X, BookOpen
} from 'lucide-react';

export default function Dashboard() {
  const router = useRouter();
  
  // Zustand State
  const {
    token, user, projects, activeProject, renders, models, loading, wsConnected,
    fetchUser, fetchProjects, setActiveProject, createProject,
    fetchAssets, uploadAsset, fetchRenders, triggerRender, 
    cancelRender, retryRender, fetchModels, downloadModel, switchModel, logout
  } = useStore();

  // Generation Panel Parameters State
  const [jobType, setJobType] = useState('text-to-video');
  const [prompt, setPrompt] = useState('');
  const [negativePrompt, setNegativePrompt] = useState('');
  const [aspectRatio, setAspectRatio] = useState('16:9');
  const [duration, setDuration] = useState(5);
  
  // Advanced Settings
  const [modelId, setModelId] = useState('svd-xt');
  const [steps, setSteps] = useState(25);
  const [cfgScale, setCfgScale] = useState(7.5);
  const [seed, setSeed] = useState<string>('');
  const [motionStrength, setMotionStrength] = useState(127);
  const [fps, setFps] = useState(8);

  // File Uploads
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [uploadedAssetId, setUploadedAssetId] = useState<number | null>(null);

  // Modals & UI States
  const [showProjModal, setShowProjModal] = useState(false);
  const [newProjName, setNewProjName] = useState('');
  const [newProjDesc, setNewProjDesc] = useState('');
  const [activeMetaJob, setActiveMetaJob] = useState<RenderJob | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Auth Guard & Mount loader
  useEffect(() => {
    if (!token) {
      router.push('/');
    } else {
      fetchUser();
      fetchProjects();
      fetchModels();
    }
  }, [token]);

  // Load project-specific data when active project changes
  useEffect(() => {
    if (activeProject) {
      fetchAssets(activeProject.id);
      fetchRenders(activeProject.id);
    }
  }, [activeProject]);

  const handleEnhancePrompt = async () => {
    if (!prompt) return;
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const res = await fetch(`${API_BASE_URL}/prompt/enhance?prompt_in=${encodeURIComponent(prompt)}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to enhance prompt');
      const data = await res.json();
      
      const enhancedText = `A high quality, ${data.style} shot of a ${data.subject} ${data.action} on a ${data.location} under a beautiful ${data.lighting} with ${data.weather} conditions. Emotion: ${data.emotion}. Camera: ${data.camera}.`;
      setPrompt(enhancedText);
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setSelectedFile(file);
    setUploadingFile(true);
    try {
      const asset = await uploadAsset(file, activeProject?.id);
      setUploadedAssetId(asset.id);
    } catch (err) {
      console.error('File upload failed', err);
    } finally {
      setUploadingFile(false);
    }
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjName) return;
    try {
      await createProject(newProjName, newProjDesc);
      setNewProjName('');
      setNewProjDesc('');
      setShowProjModal(false);
    } catch (err) {
      console.error('Failed to create project', err);
    }
  };

  const handleTriggerRender = async () => {
    if (!prompt) return;
    try {
      await triggerRender({
        job_type: jobType,
        prompt,
        negative_prompt: negativePrompt || undefined,
        aspect_ratio: aspectRatio,
        duration: duration,
        steps: steps,
        cfg_scale: cfgScale,
        seed: seed ? parseInt(seed) : undefined,
        motion_strength: motionStrength,
        fps: fps,
        model_version: modelId,
        project_id: activeProject?.id,
        input_asset_id: uploadedAssetId || undefined
      });
      setPrompt('');
      setNegativePrompt('');
      setSelectedFile(null);
      setUploadedAssetId(null);
      setSeed('');
    } catch (err: any) {
      alert(err.message || 'Error triggering render');
    }
  };

  // Presets modifiers append helpers
  const applyStylePreset = (styleName: string) => {
    setPrompt(prev => {
      const cleaned = prev.replace(/, featuring .* style/i, '');
      return `${cleaned}, featuring ${styleName} style`;
    });
  };

  const applyCameraPreset = (camName: string) => {
    setPrompt(prev => {
      const cleaned = prev.replace(/, with .* camera movement/i, '');
      return `${cleaned}, with ${camName} camera movement`;
    });
  };

  if (!token || !user) {
    return (
      <div className="flex-1 flex items-center justify-center bg-background text-white">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span>Redirecting to workspace...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-screen relative z-10">
      {/* Background decorations */}
      <div className="absolute top-10 left-1/4 glowing-orb bg-primary/10" />
      <div className="absolute bottom-20 right-1/4 glowing-orb bg-secondary/10" />

      {/* TOP HEADER */}
      <header className="h-16 border-b border-white/5 bg-black/40 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-20">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-tr from-primary to-secondary rounded-lg flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold tracking-wider bg-gradient-to-r from-white to-zinc-400 bg-clip-text text-transparent">
              AETHERIA AI
            </span>
          </div>

          <div className="h-4 w-px bg-white/10" />

          {/* Project Selector */}
          <div className="flex items-center gap-2">
            <select
              value={activeProject?.id || ''}
              onChange={(e) => {
                const proj = projects.find(p => p.id === parseInt(e.target.value));
                if (proj) setActiveProject(proj);
              }}
              className="bg-zinc-900 border border-white/10 text-sm text-zinc-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-primary/50"
            >
              {projects.map((proj) => (
                <option key={proj.id} value={proj.id}>{proj.name}</option>
              ))}
            </select>
            <button
              onClick={() => setShowProjModal(true)}
              className="p-1.5 bg-white/5 border border-white/10 hover:border-white/20 text-zinc-300 rounded-lg cursor-pointer transition"
              title="Create New Project"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* WebSocket Status bar */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs bg-white/5 border border-white/5">
            <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            <span className="text-zinc-400 font-medium">{wsConnected ? 'WebSockets Streaming Live' : 'Disconnected'}</span>
          </div>

          {/* Credit display */}
          <div className="flex items-center gap-2 bg-primary/10 border border-primary/20 px-3 py-1.5 rounded-full" title="Your Remaining Credits">
            <CreditCard className="w-4 h-4 text-primary" />
            <span className="text-xs font-semibold text-primary-foreground">{user.credits.toFixed(1)} Credits</span>
          </div>

          {/* User info */}
          <div className="flex items-center gap-2 bg-white/5 border border-white/10 px-3 py-1.5 rounded-lg">
            <UserCheck className="w-4 h-4 text-zinc-400" />
            <span className="text-xs text-zinc-300 font-medium">{user.username}</span>
          </div>

          {/* Logout */}
          <button
            onClick={logout}
            className="p-2 bg-red-950/20 border border-red-500/20 hover:border-red-500/50 hover:bg-red-950/40 text-red-400 rounded-lg cursor-pointer transition"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* DASHBOARD GRID */}
      <div className="flex-1 flex overflow-hidden">
        {/* SIDEBAR NAVIGATION */}
        <aside className="w-60 border-r border-white/5 bg-black/20 flex flex-col p-4 gap-2">
          <div className="text-xs font-semibold text-zinc-500 tracking-wider px-3 mb-2">GENERATION SUITE</div>
          
          <button
            onClick={() => setJobType('text-to-video')}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition cursor-pointer ${
              jobType === 'text-to-video' ? 'bg-primary/20 border border-primary/30 text-white font-medium' : 'text-zinc-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Film className="w-4 h-4" />
            Text-to-Video
          </button>

          <button
            onClick={() => setJobType('image-to-video')}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition cursor-pointer ${
              jobType === 'image-to-video' ? 'bg-primary/20 border border-primary/30 text-white font-medium' : 'text-zinc-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <ImageIcon className="w-4 h-4" />
            Image-to-Video
          </button>

          <div className="text-xs font-semibold text-zinc-500 tracking-wider px-3 mt-6 mb-2">ACTIVE AI MODELS</div>
          
          {/* Installed models status indicators */}
          <div className="flex flex-col gap-2 p-2">
            {models.map(model => (
              <div key={model.id} className="glass-panel p-2.5 rounded-lg text-[10px] flex flex-col gap-1 border border-white/5 bg-black/10">
                <div className="flex justify-between items-center font-bold text-zinc-200">
                  <span>{model.id.toUpperCase()}</span>
                  <span className={`px-1.5 py-0.5 rounded-full ${model.active ? 'bg-green-950/40 text-green-400 border border-green-500/30' : 'bg-zinc-800 text-zinc-400'}`}>
                    {model.active ? 'Active' : model.loaded ? 'Loaded' : 'Idle'}
                  </span>
                </div>
                <span className="text-zinc-400 truncate text-[9px]">{model.repo_id}</span>
                
                {/* Download/Switch actions */}
                <div className="flex gap-2 mt-1.5">
                  {!model.cached && (
                    <button
                      onClick={() => downloadModel(model.id)}
                      className="flex-1 py-1 rounded bg-primary/20 border border-primary/30 text-white text-[9px] hover:bg-primary/30 cursor-pointer"
                    >
                      Download Model
                    </button>
                  )}
                  {model.cached && !model.active && (
                    <button
                      onClick={() => switchModel(model.id)}
                      className="flex-1 py-1 rounded bg-zinc-800 border border-white/10 text-zinc-200 text-[9px] hover:bg-zinc-700 cursor-pointer"
                    >
                      Load pipeline
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="text-xs font-semibold text-zinc-500 tracking-wider px-3 mt-6 mb-2">SYSTEM HEALTH</div>

          <div className="glass-panel p-3.5 rounded-xl border border-white/5 flex flex-col gap-2 bg-black/40">
            <div className="flex items-center gap-2 text-xs font-semibold text-zinc-400">
              <Cpu className="w-3.5 h-3.5 text-secondary" />
              <span>VRAM Utilization</span>
            </div>
            <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
              <div className="bg-gradient-to-r from-primary to-secondary h-full rounded-full animate-pulse" style={{ width: '42%' }} />
            </div>
            <span className="text-[10px] text-zinc-500">Node cluster is running healthy.</span>
          </div>
        </aside>

        {/* WORKSPACE AREA */}
        <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden bg-black/10">
          
          {/* INPUT FORM CONTROLS */}
          <div className="lg:col-span-5 p-6 border-r border-white/5 flex flex-col gap-5 overflow-y-auto max-h-[calc(100vh-4rem)]">
            <div className="flex flex-col">
              <h2 className="text-lg font-bold text-white tracking-wide capitalize">
                {jobType.replace(/-/g, ' ')} Workstation
              </h2>
              <p className="text-xs text-zinc-400 mt-1">
                Configure your generation settings and prompt specifications below.
              </p>
            </div>

            {/* Model Target selection */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-zinc-400">Target Model Pipeline</label>
              <select
                value={modelId}
                onChange={(e) => setModelId(e.target.value)}
                className="bg-zinc-900 border border-white/10 text-sm text-zinc-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-primary/50"
              >
                <option value="svd-xt">Stable Video Diffusion img2vid-xt</option>
                <option value="cogvideox-2b">CogVideoX 2B (T2V)</option>
                <option value="ltx-video">LTX-Video Pipeline (T2V/I2V)</option>
              </select>
            </div>

            {/* Prompt Area */}
            <div className="flex flex-col gap-2">
              <div className="flex justify-between items-center">
                <label className="text-sm font-semibold text-zinc-300">Prompt Instructions</label>
                <button
                  onClick={handleEnhancePrompt}
                  disabled={!prompt}
                  className="text-xs text-primary hover:underline cursor-pointer flex items-center gap-1.5 font-medium disabled:opacity-50"
                  title="Enhance Prompt using AI Engine"
                >
                  <RefreshCw className="w-3 h-3 animate-pulse" />
                  AI Enhance
                </button>
              </div>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={3}
                className="w-full p-3 rounded-lg glass-input text-sm resize-none"
                placeholder="A stunning girl walking on a tropical beach during a golden sunset, tracking shot..."
              />
            </div>

            {/* Presets Grid */}
            <div className="flex flex-col gap-1.5">
              <span className="text-xs font-semibold text-zinc-400">Platform Presets</span>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-[10px] text-zinc-500 block mb-1">Style Presets</span>
                  <div className="flex flex-wrap gap-1">
                    {['cinematic', 'anime', 'claymation', '3d render'].map(st => (
                      <button
                        key={st}
                        onClick={() => applyStylePreset(st)}
                        className="text-[9px] px-2 py-0.5 rounded bg-white/5 border border-white/5 hover:border-white/20 text-zinc-300 transition cursor-pointer"
                      >
                        {st}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <span className="text-[10px] text-zinc-500 block mb-1">Camera Motion</span>
                  <div className="flex flex-wrap gap-1">
                    {['zoom in', 'pan shot', 'drone shot', 'static'].map(cam => (
                      <button
                        key={cam}
                        onClick={() => applyCameraPreset(cam)}
                        className="text-[9px] px-2 py-0.5 rounded bg-white/5 border border-white/5 hover:border-white/20 text-zinc-300 transition cursor-pointer"
                      >
                        {cam}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* File Upload for Image/Video inputs */}
            {(jobType === 'image-to-video' || jobType === 'video-to-video') && (
              <div className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-zinc-300">
                  {jobType === 'image-to-video' ? 'Reference Image' : 'Source Video'}
                </label>
                <div className="border border-dashed border-white/10 rounded-lg p-3 bg-white/5 flex flex-col items-center justify-center gap-2 relative overflow-hidden">
                  <input
                    type="file"
                    accept={jobType === 'image-to-video' ? 'image/*' : 'video/*'}
                    onChange={handleFileUpload}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                  <UploadCloud className="w-6 h-6 text-zinc-500" />
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">
                      {selectedFile ? selectedFile.name : `Click to upload ${jobType === 'image-to-video' ? 'image' : 'video'}`}
                    </span>
                    {uploadingFile && <span className="text-[10px] text-primary block mt-0.5">Uploading and validating...</span>}
                  </div>
                </div>
              </div>
            )}

            {/* Parameters Selection */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-zinc-400">Aspect Ratio</label>
                <select
                  value={aspectRatio}
                  onChange={(e) => setAspectRatio(e.target.value)}
                  className="bg-zinc-900 border border-white/10 text-sm text-zinc-200 rounded-lg px-2.5 py-1 focus:outline-none focus:border-primary/50"
                >
                  <option value="16:9">16:9 Cinema</option>
                  <option value="9:16">9:16 Vertical</option>
                  <option value="1:1">1:1 Square</option>
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-zinc-400">Duration ({duration}s)</label>
                <input
                  type="range"
                  min={5}
                  max={20}
                  step={5}
                  value={duration}
                  onChange={(e) => setDuration(parseInt(e.target.value))}
                  className="w-full accent-primary bg-zinc-700 h-1 rounded-lg mt-2 cursor-pointer"
                />
              </div>
            </div>

            {/* Toggle Advanced settings */}
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-xs text-zinc-400 hover:text-white flex items-center gap-1.5 font-medium cursor-pointer w-fit mt-1"
            >
              <Sliders className="w-3.5 h-3.5" />
              {showAdvanced ? 'Hide Advanced Options' : 'Show Advanced Options'}
            </button>

            {showAdvanced && (
              <div className="p-4 bg-white/5 border border-white/5 rounded-xl space-y-4 animate-fadeIn">
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-semibold text-zinc-400">Sampling Steps ({steps})</label>
                    <input
                      type="range"
                      min={10}
                      max={50}
                      step={5}
                      value={steps}
                      onChange={(e) => setSteps(parseInt(e.target.value))}
                      className="w-full accent-primary h-1 rounded-lg cursor-pointer"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-semibold text-zinc-400">CFG Guidance ({cfgScale})</label>
                    <input
                      type="range"
                      min={1}
                      max={20}
                      step={0.5}
                      value={cfgScale}
                      onChange={(e) => setCfgScale(parseFloat(e.target.value))}
                      className="w-full accent-primary h-1 rounded-lg cursor-pointer"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-semibold text-zinc-400">Motion Strength ({motionStrength})</label>
                    <input
                      type="range"
                      min={1}
                      max={255}
                      value={motionStrength}
                      onChange={(e) => setMotionStrength(parseInt(e.target.value))}
                      className="w-full accent-primary h-1 rounded-lg cursor-pointer"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-semibold text-zinc-400">Inference FPS</label>
                    <select
                      value={fps}
                      onChange={(e) => setFps(parseInt(e.target.value))}
                      className="bg-zinc-900 border border-white/10 text-xs text-zinc-300 rounded px-2 py-1 focus:outline-none"
                    >
                      <option value={8}>8 FPS</option>
                      <option value={12}>12 FPS</option>
                      <option value={16}>16 FPS</option>
                      <option value={24}>24 FPS</option>
                    </select>
                  </div>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-semibold text-zinc-400">Random Seed (Optional)</label>
                  <input
                    type="number"
                    value={seed}
                    onChange={(e) => setSeed(e.target.value)}
                    className="w-full px-2.5 py-1 rounded glass-input text-xs"
                    placeholder="Auto random seed"
                  />
                </div>
                
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-semibold text-zinc-400">Negative Prompt Override</label>
                  <input
                    type="text"
                    value={negativePrompt}
                    onChange={(e) => setNegativePrompt(e.target.value)}
                    className="w-full px-2.5 py-1 rounded glass-input text-xs"
                    placeholder="Blurry, raw drawings, static..."
                  />
                </div>
              </div>
            )}

            {/* Trigger Button */}
            <button
              onClick={handleTriggerRender}
              disabled={!prompt || loading || uploadingFile}
              className="w-full py-3 rounded-lg text-white font-semibold text-sm glow-btn cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className="w-4 h-4 fill-white" />
              Generate Video
            </button>
          </div>

          {/* RENDER RUNNING STATUS AND HISTORY */}
          <div className="lg:col-span-7 p-6 flex flex-col gap-6 overflow-y-auto max-h-[calc(100vh-4rem)]">
            <div className="flex flex-col">
              <h2 className="text-lg font-bold text-white tracking-wide">
                Render Queue & Generations
              </h2>
              <p className="text-xs text-zinc-400 mt-1">
                View your current running jobs and generation database output.
              </p>
            </div>

            {/* Render List */}
            <div className="flex flex-col gap-4">
              {renders.length === 0 ? (
                <div className="h-64 border border-dashed border-white/5 rounded-xl flex flex-col items-center justify-center text-zinc-500 gap-2 bg-black/10">
                  <Film className="w-8 h-8 opacity-40" />
                  <span className="text-sm">No render jobs recorded yet.</span>
                </div>
              ) : (
                renders.map((job) => (
                  <div key={job.id} className="glass-panel p-4.5 rounded-xl border border-white/5 flex flex-col gap-3 relative bg-black/40">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-zinc-800 border border-white/5 flex items-center justify-center">
                          {job.job_type === 'text-to-video' ? (
                            <Film className="w-4 h-4 text-zinc-300" />
                          ) : (
                            <ImageIcon className="w-4 h-4 text-zinc-300" />
                          )}
                        </div>
                        <div className="flex flex-col">
                          <span className="text-xs text-zinc-400 font-semibold uppercase">{job.job_type.replace(/-/g, ' ')}</span>
                          <span className="text-[10px] text-zinc-500 mt-0.5">ID: {job.id} • {new Date(job.created_at).toLocaleTimeString()}</span>
                        </div>
                      </div>

                      {/* Status indicator */}
                      <div className="flex items-center gap-2">
                        {job.status === 'PENDING' && (
                          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-yellow-950/40 border border-yellow-500/30 text-yellow-400 rounded-full text-[10px] font-semibold animate-pulse">
                            <RefreshCw className="w-3 h-3 animate-spin" />
                            <span>Queued</span>
                          </div>
                        )}
                        {job.status === 'RUNNING' && (
                          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-blue-950/40 border border-blue-500/30 text-blue-400 rounded-full text-[10px] font-semibold">
                            <Activity className="w-3 h-3 animate-pulse" />
                            <span>Rendering ({job.progress}%)</span>
                          </div>
                        )}
                        {job.status === 'SUCCESS' && (
                          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-green-950/40 border border-green-500/30 text-green-400 rounded-full text-[10px] font-semibold">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Ready</span>
                          </div>
                        )}
                        {job.status === 'FAILED' && (
                          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-red-950/40 border border-red-500/30 text-red-400 rounded-full text-[10px] font-semibold" title={job.error_message || ''}>
                            <AlertCircle className="w-3 h-3" />
                            <span>Failed</span>
                          </div>
                        )}
                        {job.status === 'CANCELLED' && (
                          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-zinc-800 border border-white/10 text-zinc-400 rounded-full text-[10px] font-semibold">
                            <X className="w-3 h-3" />
                            <span>Cancelled</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="text-xs text-zinc-300 leading-relaxed italic bg-white/5 p-2.5 rounded-lg border border-white/5">
                      &ldquo;{job.prompt}&rdquo;
                    </div>

                    {/* Progress Bar for Active Jobs */}
                    {(job.status === 'PENDING' || job.status === 'RUNNING') && (
                      <div className="flex items-center gap-4 w-full">
                        <div className="flex-1 bg-white/5 h-1.5 rounded-full overflow-hidden">
                          <div 
                            className="bg-gradient-to-r from-primary to-secondary h-full rounded-full transition-all duration-500" 
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                        {job.status === 'RUNNING' && (
                          <button
                            onClick={() => cancelRender(job.id)}
                            className="text-[10px] text-red-400 hover:text-red-300 font-semibold cursor-pointer border border-red-500/20 px-2 py-0.5 rounded bg-red-950/20 hover:bg-red-950/40 transition"
                          >
                            Cancel
                          </button>
                        )}
                      </div>
                    )}

                    {/* Action controls for failed/cancelled jobs */}
                    {(job.status === 'FAILED' || job.status === 'CANCELLED') && (
                      <div className="flex justify-end mt-1">
                        <button
                          onClick={() => retryRender(job.id)}
                          className="text-[10px] text-primary hover:text-white font-semibold cursor-pointer border border-primary/20 px-2.5 py-1 rounded bg-primary/10 hover:bg-primary/20 transition flex items-center gap-1"
                        >
                          <RefreshCw className="w-3 h-3" />
                          Retry Generation
                        </button>
                      </div>
                    )}

                    {/* Video Output display for successful jobs */}
                    {job.status === 'SUCCESS' && job.result_url && (
                      <div className="flex flex-col gap-2">
                        <div className="aspect-video bg-black/60 rounded-lg border border-white/5 relative overflow-hidden flex items-center justify-center group">
                          {/* SVD looping visual preview using loop gif or mp4 stream */}
                          {job.gif_url ? (
                            <img
                              src={job.gif_url}
                              alt="Loop preview"
                              className="w-full h-full object-cover group-hover:hidden"
                            />
                          ) : job.thumbnail_url ? (
                            <img
                              src={job.thumbnail_url}
                              alt="Thumbnail preview"
                              className="w-full h-full object-cover group-hover:hidden"
                            />
                          ) : null}
                          <video 
                            src={job.result_url} 
                            controls 
                            className="w-full h-full object-cover hidden group-hover:block"
                            poster={job.thumbnail_url || undefined}
                          />
                          <div className="absolute top-2 right-2 bg-black/60 backdrop-blur px-2 py-0.5 rounded text-[9px] text-zinc-300 group-hover:hidden flex items-center gap-1">
                            <Eye className="w-3 h-3 text-primary" /> Hover to Play
                          </div>
                        </div>
                        
                        <div className="flex justify-between items-center mt-1">
                          <span className="text-[10px] text-zinc-500">
                            Seed: {job.seed} | CFG: {job.cfg_scale} | Steps: {job.steps}
                          </span>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => setActiveMetaJob(job)}
                              className="text-[10px] font-semibold text-zinc-300 px-2.5 py-1 bg-white/5 border border-white/10 hover:border-white/20 rounded-lg flex items-center gap-1 transition cursor-pointer"
                            >
                              <BookOpen className="w-3.5 h-3.5" />
                              Metadata
                            </button>
                            <a
                              href={job.result_url}
                              download={`render_${job.id}.mp4`}
                              target="_blank"
                              className="text-[10px] font-semibold text-white px-2.5 py-1 bg-white/5 border border-white/10 hover:border-white/20 rounded-lg flex items-center gap-1 transition cursor-pointer"
                            >
                              <Download className="w-3.5 h-3.5" />
                              Download
                            </a>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </main>
      </div>

      {/* CREATE PROJECT MODAL */}
      {showProjModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md p-6 rounded-xl glass-panel relative overflow-hidden bg-zinc-950">
            <h3 className="text-lg font-bold text-white mb-4">Create New Project</h3>
            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="block text-zinc-300 text-sm font-medium mb-1.5">Project Name</label>
                <input
                  type="text"
                  required
                  value={newProjName}
                  onChange={(e) => setNewProjName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg glass-input text-sm"
                  placeholder="e.g. Cinematic Promo Video"
                />
              </div>
              <div>
                <label className="block text-zinc-300 text-sm font-medium mb-1.5">Description (Optional)</label>
                <textarea
                  value={newProjDesc}
                  onChange={(e) => setNewProjDesc(e.target.value)}
                  className="w-full p-3 rounded-lg glass-input text-sm resize-none"
                  rows={3}
                  placeholder="Describe your workspace parameters..."
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowProjModal(false)}
                  className="px-4 py-2 border border-white/10 text-zinc-400 text-sm rounded-lg hover:bg-white/5 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-white text-sm font-medium rounded-lg glow-btn cursor-pointer"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* METADATA INSPECTOR MODAL */}
      {activeMetaJob && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-xl p-6 rounded-xl glass-panel relative bg-zinc-950 border border-white/10 animate-fadeIn">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-md font-bold text-white flex items-center gap-2">
                <Settings className="w-4 h-4 text-primary" />
                Render Configuration Metadata
              </h3>
              <button 
                onClick={() => setActiveMetaJob(null)}
                className="text-zinc-400 hover:text-white cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="bg-black/60 p-4 rounded-lg overflow-x-auto max-h-[60vh] border border-white/5">
              <pre className="text-xs text-green-400 font-mono">
                {JSON.stringify({
                  job_id: activeMetaJob.id,
                  model_version: activeMetaJob.model_version || 'svd-xt',
                  aspect_ratio: activeMetaJob.aspect_ratio,
                  fps: activeMetaJob.fps,
                  duration_sec: activeMetaJob.duration,
                  guidance_cfg: activeMetaJob.cfg_scale,
                  sampling_steps: activeMetaJob.steps,
                  motion_bucket_strength: activeMetaJob.motion_strength,
                  resolved_seed: activeMetaJob.seed,
                  prompt_specification: activeMetaJob.prompt,
                  negative_prompt_specification: activeMetaJob.negative_prompt,
                  creation_timestamp: activeMetaJob.created_at,
                  asset_mp4_url: activeMetaJob.result_url,
                  thumbnail_jpg_url: activeMetaJob.thumbnail_url,
                  preview_gif_url: activeMetaJob.gif_url,
                  metadata_json_url: activeMetaJob.metadata_url
                }, null, 2)}
              </pre>
            </div>
            <div className="flex justify-end gap-3 mt-4">
              {activeMetaJob.metadata_url && (
                <a
                  href={activeMetaJob.metadata_url}
                  target="_blank"
                  className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-zinc-300 text-xs rounded-lg transition"
                >
                  Raw Metadata JSON
                </a>
              )}
              <button
                onClick={() => setActiveMetaJob(null)}
                className="px-4 py-2 bg-primary text-white text-xs font-medium rounded-lg cursor-pointer"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
