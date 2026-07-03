/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useStore, TimelineItem } from '../store';
import { 
  ArrowLeft, Plus, Trash2, Film, Music, AlignLeft,
  Settings, Sparkles, Activity, Clock, FileText
} from 'lucide-react';
import Link from 'next/link';

function TimelineContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const storyboardId = searchParams.get('storyboard_id');

  const {
    token, activeStoryboard, assets, subtitles,
    fetchStoryboardDetails, fetchAssets, addTimelineItem, deleteTimelineItem,
    fetchSubtitles, createSubtitle, deleteSubtitle
  } = useStore();

  const [activeLayerId, setActiveLayerId] = useState<number | null>(null);
  const [selectedShotId, setSelectedShotId] = useState<string>('');
  const [selectedAssetId, setSelectedAssetId] = useState<string>('');
  const [startTime, setStartTime] = useState(0);
  const [duration, setDuration] = useState(5);
  const [transitionIn, setTransitionIn] = useState('none');
  const [transitionOut, setTransitionOut] = useState('none');

  // Subtitle custom inputs states
  const [subText, setSubText] = useState('');
  const [subStart, setSubStart] = useState(0);
  const [subEnd, setSubEnd] = useState(5);

  // Keyframes configurations states
  const [kfTime, setKfTime] = useState(0.0);
  const [kfScale, setKfScale] = useState(1.0);
  const [kfOpacity, setKfOpacity] = useState(1.0);
  const [kfs, setKfs] = useState<Array<{ time: number; scale: number; opacity: number }>>([]);

  useEffect(() => {
    if (!token) {
      router.push('/');
    } else if (storyboardId) {
      fetchStoryboardDetails(parseInt(storyboardId));
      fetchAssets();
      fetchSubtitles(parseInt(storyboardId));
    }
  }, [token, storyboardId]);

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (activeLayerId === null || !storyboardId) return;
    try {
      await addTimelineItem(activeLayerId, {
        shot_id: selectedShotId ? parseInt(selectedShotId) : null,
        asset_id: selectedAssetId ? parseInt(selectedAssetId) : null,
        start_time: startTime,
        duration: duration,
        transition_in: transitionIn !== 'none' ? transitionIn : null,
        transition_out: transitionOut !== 'none' ? transitionOut : null
      });
      setSelectedShotId('');
      setSelectedAssetId('');
      setStartTime(0);
      setDuration(5);
      setTransitionIn('none');
      setTransitionOut('none');
      setActiveLayerId(null);
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddSubtitle = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subText || !storyboardId) return;
    try {
      await createSubtitle({
        text: subText,
        start_time: subStart,
        end_time: subEnd,
        storyboard_id: parseInt(storyboardId),
        render_job_id: null
      });
      setSubText('');
      setSubStart(subEnd);
      setSubEnd(subEnd + 5);
    } catch (err) {
      console.error(err);
    }
  };

  if (!storyboardId || !activeStoryboard) {
    return (
      <div className="flex-1 flex items-center justify-center bg-background text-zinc-400">
        <span>No active storyboard reference provided.</span>
      </div>
    );
  }

  const allShots = activeStoryboard.scenes.flatMap(s => s.shots);

  return (
    <div className="flex-1 min-h-screen bg-background text-white p-6 relative">
      <div className="absolute top-10 left-1/3 glowing-orb bg-secondary/10" />

      {/* TOP HEADER */}
      <div className="flex items-center justify-between mb-8 relative z-10 border-b border-white/5 pb-4">
        <div className="flex items-center gap-3">
          <Link href={`/storyboard`} className="p-2 hover:bg-white/5 rounded-lg border border-white/5 text-zinc-300 transition">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-wide flex items-center gap-2">
              <Settings className="w-5 h-5 text-secondary" />
              Multi-track Studio Timeline
            </h1>
            <p className="text-xs text-zinc-400">Configure transitions, layers, and audio/video sync tracks for: {activeStoryboard.name}</p>
          </div>
        </div>
      </div>

      {/* STUDIO LAYOUT */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 relative z-10">
        
        {/* TIMELINE OVERVIEW - TRACKS */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          <div className="glass-panel p-6 rounded-xl border border-white/5 bg-black/40 flex flex-col gap-6">
            <div className="flex justify-between items-center text-xs text-zinc-400 font-semibold uppercase tracking-wider">
              <span className="flex items-center gap-1.5"><Clock className="w-4 h-4 text-zinc-500" /> Layer Sequencing Tracks</span>
              <span>Render status: <span className="text-primary font-bold">{activeStoryboard.status}</span></span>
            </div>

            {/* Timeline tracks blocks */}
            <div className="space-y-4">
              {activeStoryboard.timeline?.layers.map(layer => {
                const Icon = layer.layer_type === 'video' ? Film 
                            : layer.layer_type === 'audio' ? Music 
                            : AlignLeft;
                            
                return (
                  <div key={layer.id} className="grid grid-cols-12 gap-4 items-center">
                    
                    {/* Track label */}
                    <div className="col-span-3 xl:col-span-3 p-3 bg-white/5 rounded-lg border border-white/5 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Icon className="w-4 h-4 text-zinc-400" />
                        <span className="text-xs font-semibold">{layer.name}</span>
                      </div>
                      <button
                        onClick={() => setActiveLayerId(layer.id)}
                        className="p-1 hover:bg-white/10 text-zinc-400 hover:text-white rounded"
                      >
                        <Plus className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    {/* Track content block */}
                    <div className="col-span-9 xl:col-span-9 min-h-[50px] p-2 bg-black/60 rounded-lg border border-white/5 flex gap-2 overflow-x-auto relative items-center">
                      
                      <div className="absolute inset-0 flex justify-between pointer-events-none opacity-[0.03]">
                        {Array.from({ length: 12 }).map((_, i) => (
                          <div key={i} className="w-px h-full bg-white" />
                        ))}
                      </div>

                      {layer.items.length === 0 ? (
                        <span className="text-[10px] text-zinc-600 pl-2">No items added to this track. Click plus to add items.</span>
                      ) : (
                        layer.items.map(item => {
                          const itemShot = allShots.find(s => s.id === item.shot_id);
                          const label = itemShot ? itemShot.name : 'Asset item';
                          
                          return (
                            <div 
                              key={item.id} 
                              className="h-9 px-3 rounded bg-secondary/20 border border-secondary/40 text-[10px] text-zinc-200 flex items-center justify-between gap-4 select-none relative z-10"
                              style={{ minWidth: `${item.duration * 20}px` }}
                            >
                              <div className="flex flex-col">
                                <span className="font-bold truncate max-w-[120px]">{label}</span>
                                <span className="text-[8px] text-zinc-500 mt-0.5">{item.start_time}s - {item.start_time + item.duration}s</span>
                              </div>
                              
                              {item.transition_out && (
                                <span className="px-1 py-0.5 rounded bg-zinc-800 text-[6px] text-zinc-400 capitalize">{item.transition_out}</span>
                              )}
                              
                              <button
                                onClick={() => deleteTimelineItem(item.id)}
                                className="p-0.5 hover:text-red-400 text-zinc-500 rounded"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          );
                        })
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* SIDE PANEL */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          
          {/* SUBTITLE MANAGER PANEL */}
          <div className="glass-panel p-5 rounded-xl border border-white/5 bg-black/40 flex flex-col gap-4">
            <h2 className="text-sm font-bold text-zinc-300 uppercase tracking-wider flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-primary" /> Storyboard Subtitles
            </h2>

            <form onSubmit={handleAddSubtitle} className="space-y-3">
              <div>
                <label className="text-[10px] text-zinc-400 block mb-1">Subtitle Text</label>
                <input
                  type="text"
                  required
                  value={subText}
                  onChange={(e) => setSubText(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
                  placeholder="Dialogue or narrations..."
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] text-zinc-400 block mb-1">Start Time (s)</label>
                  <input
                    type="number"
                    step={0.1}
                    required
                    value={subStart}
                    onChange={(e) => setSubStart(parseFloat(e.target.value))}
                    className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-zinc-400 block mb-1">End Time (s)</label>
                  <input
                    type="number"
                    step={0.1}
                    required
                    value={subEnd}
                    onChange={(e) => setSubEnd(parseFloat(e.target.value))}
                    className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
                  />
                </div>
              </div>
              <button
                type="submit"
                className="w-full py-1.5 bg-white/5 border border-white/10 hover:border-white/20 text-xs font-semibold rounded-lg flex items-center justify-center gap-1 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" /> Add Timed Subtitle
              </button>
            </form>

            <div className="border-t border-white/5 pt-3 max-h-40 overflow-y-auto space-y-2">
              {subtitles.length === 0 ? (
                <span className="text-[10px] text-zinc-500">No subtitles generated yet.</span>
              ) : (
                subtitles.map(sub => (
                  <div key={sub.id} className="p-2 rounded bg-white/5 border border-white/5 flex justify-between items-center text-zinc-300">
                    <div className="flex flex-col min-w-0">
                      <span className="text-xs italic truncate font-medium">&ldquo;{sub.text}&rdquo;</span>
                      <span className="text-[8px] text-zinc-500 mt-0.5">{sub.start_time}s - {sub.end_time}s</span>
                    </div>
                    <button
                      onClick={() => deleteSubtitle(sub.id)}
                      className="p-1 hover:text-red-400 text-zinc-500 rounded"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* KEYFRAME CANVAS EDITOR */}
          <div className="glass-panel p-5 rounded-xl border border-white/5 bg-black/40 flex flex-col gap-4">
            <h2 className="text-sm font-bold text-zinc-300 uppercase tracking-wider flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-secondary" /> Keyframe Opacity & Scale
            </h2>
            <div className="space-y-3">
              <div>
                <label className="text-[10px] text-zinc-400 block mb-1">Time Position (s)</label>
                <input
                  type="number"
                  step={0.5}
                  value={kfTime}
                  onChange={(e) => setKfTime(parseFloat(e.target.value))}
                  className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] text-zinc-400 block mb-1">Scale Multiplier</label>
                  <input
                    type="number"
                    step={0.1}
                    value={kfScale}
                    onChange={(e) => setKfScale(parseFloat(e.target.value))}
                    className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-zinc-400 block mb-1">Opacity Ratio</label>
                  <input
                    type="number"
                    step={0.1}
                    min={0}
                    max={1}
                    value={kfOpacity}
                    onChange={(e) => setKfOpacity(parseFloat(e.target.value))}
                    className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
                  />
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                   setKfs([...kfs, { time: kfTime, scale: kfScale, opacity: kfOpacity }]);
                   setKfTime(kfTime + 1);
                }}
                className="w-full py-1.5 bg-white/5 border border-white/10 hover:border-white/20 text-xs font-semibold rounded-lg flex items-center justify-center gap-1 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" /> Add Canvas Keyframe
              </button>
            </div>

            <div className="border-t border-white/5 pt-3 max-h-40 overflow-y-auto space-y-1.5 text-[10px] text-zinc-400">
               {kfs.length === 0 ? (
                  <span>No keyframes configured. Set values above.</span>
               ) : (
                  kfs.map((k, i) => (
                     <div key={i} className="flex justify-between items-center p-1 bg-white/5 rounded">
                        <span>Time: {k.time}s | Scale: {k.scale}x | Opacity: {k.opacity}</span>
                        <button onClick={() => setKfs(kfs.filter((_, idx) => idx !== i))} className="text-red-400 hover:text-red-300">Delete</button>
                     </div>
                  ))
               )}
            </div>
          </div>

        </div>

      </div>

      {/* ADD ITEM TO TRACK MODAL */}
      {activeLayerId !== null && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md p-6 rounded-xl glass-panel relative overflow-hidden bg-zinc-950 border border-white/10 animate-fadeIn">
            <h3 className="text-md font-bold text-white mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-secondary" />
              Add Track Clip
            </h3>
            <form onSubmit={handleAddItem} className="space-y-4">
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-zinc-400 text-xs mb-1.5">Select Shot Card</label>
                  <select
                    value={selectedShotId}
                    onChange={(e) => {
                      setSelectedShotId(e.target.value);
                      setSelectedAssetId('');
                    }}
                    className="w-full bg-zinc-900 border border-white/10 text-xs text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none"
                  >
                    <option value="">-- Choose Shot --</option>
                    {allShots.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-zinc-400 text-xs mb-1.5">Select Media Asset</label>
                  <select
                    value={selectedAssetId}
                    onChange={(e) => {
                      setSelectedAssetId(e.target.value);
                      setSelectedShotId('');
                    }}
                    className="w-full bg-zinc-900 border border-white/10 text-xs text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none"
                  >
                    <option value="">-- Choose Asset --</option>
                    {assets.map(a => (
                      <option key={a.id} value={a.id}>{a.original_name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-zinc-400 text-xs mb-1.5">Start Time Offset (seconds)</label>
                  <input
                    type="number"
                    required
                    min={0}
                    step={0.5}
                    value={startTime}
                    onChange={(e) => setStartTime(parseFloat(e.target.value))}
                    className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
                  />
                </div>
                <div>
                  <label className="block text-zinc-400 text-xs mb-1.5">Duration (seconds)</label>
                  <input
                    type="number"
                    required
                    min={1}
                    value={duration}
                    onChange={(e) => setDuration(parseInt(e.target.value))}
                    className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-zinc-400 text-xs mb-1.5">Transition In</label>
                  <select
                    value={transitionIn}
                    onChange={(e) => setTransitionIn(e.target.value)}
                    className="w-full bg-zinc-900 border border-white/10 text-xs text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none"
                  >
                    <option value="none">None (Cut)</option>
                    <option value="fade">Fade In</option>
                    <option value="cross-dissolve">Cross Dissolve</option>
                  </select>
                </div>
                <div>
                  <label className="block text-zinc-400 text-xs mb-1.5">Transition Out</label>
                  <select
                    value={transitionOut}
                    onChange={(e) => setTransitionOut(e.target.value)}
                    className="w-full bg-zinc-900 border border-white/10 text-xs text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none"
                  >
                    <option value="none">None (Cut)</option>
                    <option value="fade">Fade Out</option>
                    <option value="cross-dissolve">Cross Dissolve</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setActiveLayerId(null)}
                  className="px-4 py-2 border border-white/10 text-zinc-400 text-xs rounded-lg hover:bg-white/5 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!selectedShotId && !selectedAssetId}
                  className="px-4 py-2 bg-primary text-white text-xs font-semibold rounded-lg glow-btn disabled:opacity-50 cursor-pointer"
                >
                  Add to Track
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function TimelineEditor() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex items-center justify-center bg-background text-zinc-400">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-secondary border-t-transparent rounded-full animate-spin" />
          <span>Opening multi-track studio timeline...</span>
        </div>
      </div>
    }>
      <TimelineContent />
    </Suspense>
  );
}
