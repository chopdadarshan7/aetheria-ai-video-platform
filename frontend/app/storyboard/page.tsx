/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useStore, Shot } from '../store';
import { 
  Plus, Film, Video, Play, Trash2, ArrowLeft,
  Sparkles, CheckCircle2, AlertCircle, RefreshCw, Settings, LayoutGrid, Sliders
} from 'lucide-react';
import Link from 'next/link';

export default function StoryboardCreator() {
  const router = useRouter();
  const {
    token, activeProject, storyboards, activeStoryboard, loading,
    fetchStoryboards, fetchStoryboardDetails, createStoryboard, deleteStoryboard,
    createScene, deleteScene, createShot, deleteShot, triggerStoryboardRender
  } = useStore();

  const [sbName, setSbName] = useState('');
  const [sbDesc, setSbDesc] = useState('');
  
  // Scene/Shot creation state
  const [sceneName, setSceneName] = useState('');
  const [shotName, setShotName] = useState('');
  const [shotPrompt, setShotPrompt] = useState('');
  const [shotDuration, setShotDuration] = useState(5);
  const [shotModel, setShotModel] = useState('cogvideox-2b');
  const [activeSceneId, setActiveSceneId] = useState<number | null>(null);

  // Motion brush coordinates mock states
  const [camPath, setCamPath] = useState('[{"x": 0.0, "y": 0.0, "zoom": 1.0}]');
  const [motionBrush, setMotionBrush] = useState('[]');

  useEffect(() => {
    if (!token) {
      router.push('/');
    } else {
      fetchStoryboards(activeProject?.id);
    }
  }, [token, activeProject]);

  const handleCreateStoryboard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sbName) return;
    try {
      const sb = await createStoryboard(sbName, sbDesc, activeProject?.id);
      setSbName('');
      setSbDesc('');
      fetchStoryboardDetails(sb.id);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateScene = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sceneName || !activeStoryboard) return;
    try {
      await createScene(activeStoryboard.id, sceneName, activeStoryboard.scenes.length);
      setSceneName('');
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateShot = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!shotName || !shotPrompt || activeSceneId === null || !activeStoryboard) return;
    try {
      await createShot(activeSceneId, {
        name: shotName,
        prompt: shotPrompt,
        order: 0,
        negative_prompt: null,
        aspect_ratio: '16:9',
        duration: shotDuration,
        steps: 25,
        cfg_scale: 7.5,
        seed: null,
        motion_strength: 127,
        fps: 8,
        model_version: shotModel,
        camera_path: camPath,
        motion_brush: motionBrush
      });
      setShotName('');
      setShotPrompt('');
      setCamPath('[{"x": 0.0, "y": 0.0, "zoom": 1.0}]');
      setMotionBrush('[]');
      setActiveSceneId(null);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRenderStoryboard = async () => {
    if (!activeStoryboard) return;
    try {
      await triggerStoryboardRender(activeStoryboard.id);
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
              <LayoutGrid className="w-5 h-5 text-primary" />
              Storyboard Grid Creator
            </h1>
            <p className="text-xs text-zinc-400">Design multi-shot narratives with custom camera motion brushes.</p>
          </div>
        </div>

        {activeStoryboard && (
          <div className="flex gap-3">
            <Link 
              href={`/timeline?storyboard_id=${activeStoryboard.id}`}
              className="px-4 py-2 border border-white/10 hover:border-white/20 text-zinc-300 text-sm rounded-lg flex items-center gap-2 transition"
            >
              <Settings className="w-4 h-4" />
              Open Multi-track Timeline
            </Link>
            <button
              onClick={handleRenderStoryboard}
              disabled={activeStoryboard.status === 'RUNNING' || activeStoryboard.scenes.length === 0}
              className="px-4 py-2 bg-primary hover:bg-primary-hover font-semibold text-sm rounded-lg flex items-center gap-2 glow-btn disabled:opacity-50 transition cursor-pointer"
            >
              <Play className="w-4 h-4 fill-white" />
              Trigger Storyboard Render
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 relative z-10">
        
        {/* STORYBOARDS LIST */}
        <div className="lg:col-span-3 flex flex-col gap-6">
          <div className="glass-panel p-5 rounded-xl border border-white/5 bg-black/40">
            <h2 className="text-sm font-bold text-zinc-300 mb-4 uppercase tracking-wider">Create Storyboard</h2>
            <form onSubmit={handleCreateStoryboard} className="space-y-4">
              <div>
                <label className="text-[10px] text-zinc-400 block mb-1">Storyboard Name</label>
                <input
                  type="text"
                  required
                  value={sbName}
                  onChange={(e) => setSbName(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
                  placeholder="e.g. Sci-Fi Trailer"
                />
              </div>
              <div>
                <label className="text-[10px] text-zinc-400 block mb-1">Description (Optional)</label>
                <textarea
                  value={sbDesc}
                  onChange={(e) => setSbDesc(e.target.value)}
                  className="w-full p-2.5 rounded-lg glass-input text-xs resize-none"
                  rows={2}
                  placeholder="Cinematic space narrative..."
                />
              </div>
              <button
                type="submit"
                className="w-full py-2 bg-white/5 border border-white/10 hover:border-white/20 text-white font-semibold text-xs rounded-lg flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                Initialize storyboard
              </button>
            </form>
          </div>

          <div className="glass-panel p-5 rounded-xl border border-white/5 bg-black/40">
            <h2 className="text-sm font-bold text-zinc-300 mb-3 uppercase tracking-wider">Your Storyboards</h2>
            {storyboards.length === 0 ? (
              <span className="text-xs text-zinc-500">No storyboards created.</span>
            ) : (
              <div className="flex flex-col gap-2">
                {storyboards.map(sb => (
                  <div 
                    key={sb.id}
                    className={`p-3 rounded-lg border transition cursor-pointer flex justify-between items-center ${
                      activeStoryboard?.id === sb.id 
                        ? 'bg-primary/10 border-primary text-white' 
                        : 'bg-white/5 border-white/5 hover:border-white/15 text-zinc-300'
                    }`}
                    onClick={() => fetchStoryboardDetails(sb.id)}
                  >
                    <div className="flex flex-col min-w-0">
                      <span className="text-xs font-semibold truncate">{sb.name}</span>
                      <span className="text-[9px] text-zinc-500 mt-0.5 capitalize">Status: {sb.status.toLowerCase()}</span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteStoryboard(sb.id);
                      }}
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

        {/* ACTIVE STORYBOARD CREATIVE WORKSPACE */}
        <div className="lg:col-span-9 flex flex-col gap-6">
          {!activeStoryboard ? (
            <div className="h-96 border border-dashed border-white/5 rounded-xl flex flex-col items-center justify-center text-zinc-500 gap-2 bg-black/10">
              <Film className="w-12 h-12 opacity-40 text-primary" />
              <span className="text-sm">Select or create a Storyboard to open the creative workspace grid.</span>
            </div>
          ) : (
            <div className="space-y-6">
              
              {/* Storyboard Rendering status bar */}
              {activeStoryboard.status !== 'PENDING' && (
                <div className="glass-panel p-4.5 rounded-xl border border-white/5 bg-black/50 flex flex-col gap-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-zinc-300 font-semibold uppercase tracking-wider flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-primary" />
                      Storyboard Compilation: {activeStoryboard.name}
                    </span>
                    <div className="flex items-center gap-2">
                      {activeStoryboard.status === 'RUNNING' && (
                        <div className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] bg-blue-950/40 border border-blue-500/25 text-blue-400">
                          <RefreshCw className="w-3 h-3 animate-spin" /> Rendering {activeStoryboard.progress}%
                        </div>
                      )}
                      {activeStoryboard.status === 'SUCCESS' && (
                        <div className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] bg-green-950/40 border border-green-500/25 text-green-400">
                          <CheckCircle2 className="w-3 h-3" /> Ready
                        </div>
                      )}
                      {activeStoryboard.status === 'FAILED' && (
                        <div className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] bg-red-950/40 border border-red-500/25 text-red-400" title={activeStoryboard.error_message || ''}>
                          <AlertCircle className="w-3 h-3" /> Failed
                        </div>
                      )}
                    </div>
                  </div>

                  {activeStoryboard.status === 'RUNNING' && (
                    <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                      <div className="bg-gradient-to-r from-primary to-secondary h-full transition-all duration-500" style={{ width: `${activeStoryboard.progress}%` }} />
                    </div>
                  )}

                  {activeStoryboard.status === 'SUCCESS' && activeStoryboard.result_url && (
                    <div className="aspect-video w-full max-w-2xl bg-black rounded-lg border border-white/5 overflow-hidden mx-auto">
                      <video src={activeStoryboard.result_url} controls className="w-full h-full object-cover" />
                    </div>
                  )}
                </div>
              )}

              {/* GRID AREA */}
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-md font-bold text-zinc-200">Storyboard Scenes & Shots Grid</h3>
                  <form onSubmit={handleCreateScene} className="flex gap-2">
                    <input
                      type="text"
                      required
                      value={sceneName}
                      onChange={(e) => setSceneName(e.target.value)}
                      className="px-3 py-1.5 rounded-lg glass-input text-xs w-48"
                      placeholder="New Scene Name (e.g. Intro)"
                    />
                    <button
                      type="submit"
                      className="px-3 py-1.5 bg-white/5 border border-white/10 hover:border-white/20 text-xs rounded-lg flex items-center gap-1"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      Add Scene
                    </button>
                  </form>
                </div>

                {activeStoryboard.scenes.length === 0 ? (
                  <div className="h-48 border border-dashed border-white/5 rounded-xl flex items-center justify-center text-zinc-600 bg-black/5">
                    No scenes created yet. Use the input above to create one.
                  </div>
                ) : (
                  <div className="flex flex-col gap-6">
                    {activeStoryboard.scenes.map(scene => (
                      <div key={scene.id} className="glass-panel p-5 rounded-xl border border-white/5 bg-black/20 flex flex-col gap-4">
                        <div className="flex justify-between items-center border-b border-white/5 pb-2.5">
                          <span className="text-sm font-bold text-zinc-300">Scene: {scene.name}</span>
                          <div className="flex gap-2">
                            <button
                              onClick={() => setActiveSceneId(scene.id)}
                              className="px-2.5 py-1 bg-primary/20 border border-primary/30 text-white rounded text-[10px] flex items-center gap-1 cursor-pointer"
                            >
                              <Plus className="w-3 h-3" /> Add Shot Card
                            </button>
                            <button
                              onClick={() => deleteScene(scene.id)}
                              className="p-1 hover:text-red-400 text-zinc-500 rounded"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>

                        {/* Shot cards list */}
                        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                          {scene.shots.map(shot => (
                            <div key={shot.id} className="p-3.5 rounded-lg bg-white/5 border border-white/5 flex flex-col gap-2 relative group">
                              <button
                                onClick={() => deleteShot(shot.id)}
                                className="absolute top-2 right-2 p-1 text-zinc-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                              <div className="flex items-center gap-1.5">
                                <Video className="w-3.5 h-3.5 text-primary" />
                                <span className="text-xs font-semibold text-zinc-300">{shot.name}</span>
                              </div>
                              <p className="text-[10px] text-zinc-400 italic bg-black/20 p-2 rounded leading-relaxed border border-white/5">
                                &ldquo;{shot.prompt}&rdquo;
                              </p>
                              <div className="flex flex-wrap gap-1.5 mt-1 text-[8px] text-zinc-500">
                                <span className="px-1.5 py-0.5 rounded bg-zinc-800">Duration: {shot.duration}s</span>
                                <span className="px-1.5 py-0.5 rounded bg-zinc-800">Model: {shot.model_version}</span>
                                {shot.camera_path && <span className="px-1.5 py-0.5 rounded bg-zinc-800">Camera Active</span>}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ADD SHOT CARD MODAL */}
      {activeSceneId !== null && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md p-6 rounded-xl glass-panel relative overflow-hidden bg-zinc-950 border border-white/10 animate-fadeIn">
            <h3 className="text-md font-bold text-white mb-4 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-primary" />
              Configure Shot Card Parameters
            </h3>
            <form onSubmit={handleCreateShot} className="space-y-4">
              <div>
                <label className="block text-zinc-400 text-xs mb-1.5">Shot Descriptor</label>
                <input
                  type="text"
                  required
                  value={shotName}
                  onChange={(e) => setShotName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg glass-input text-xs"
                  placeholder="e.g. Medium Shot Pan Right"
                />
              </div>
              
              <div>
                <label className="block text-zinc-400 text-xs mb-1.5">Shot Instructions (Prompt)</label>
                <textarea
                  required
                  value={shotPrompt}
                  onChange={(e) => setShotPrompt(e.target.value)}
                  className="w-full p-3 rounded-lg glass-input text-xs resize-none"
                  rows={3}
                  placeholder="A cinematic spaceship zooming through nebulae clouds, photorealistic..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-zinc-400 text-xs mb-1.5">Model Version</label>
                  <select
                    value={shotModel}
                    onChange={(e) => setShotModel(e.target.value)}
                    className="w-full bg-zinc-900 border border-white/10 text-xs text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none"
                  >
                    <option value="cogvideox-2b">CogVideoX 2B</option>
                    <option value="controlnet-canny">ControlNet Canny</option>
                    <option value="sd-inpainting">SD Inpainting</option>
                  </select>
                </div>
                <div>
                  <label className="block text-zinc-400 text-xs mb-1.5">Duration (seconds)</label>
                  <select
                    value={shotDuration}
                    onChange={(e) => setShotDuration(parseInt(e.target.value))}
                    className="w-full bg-zinc-900 border border-white/10 text-xs text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none"
                  >
                    <option value={5}>5 seconds</option>
                    <option value={10}>10 seconds</option>
                    <option value={15}>15 seconds</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-zinc-400 text-xs mb-1">Camera Path Vectors (Mock coordinates)</label>
                <input
                  type="text"
                  value={camPath}
                  onChange={(e) => setCamPath(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded bg-zinc-900 text-zinc-300 border border-white/10 text-[10px]"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setActiveSceneId(null)}
                  className="px-4 py-2 border border-white/10 text-zinc-400 text-xs rounded-lg hover:bg-white/5 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-white text-xs font-semibold rounded-lg glow-btn cursor-pointer"
                >
                  Create Shot Card
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
