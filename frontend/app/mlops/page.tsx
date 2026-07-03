/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useStore, Dataset, FineTuningJob } from '../store';
import { 
  ArrowLeft, Plus, Cpu, Database, PlayCircle, Activity,
  CheckCircle2, AlertCircle, RefreshCw, Layers
} from 'lucide-react';
import Link from 'next/link';

export default function MLOpsDashboard() {
  const router = useRouter();
  const {
    token, datasets, fineTuningJobs, loading,
    fetchDatasets, createDataset, triggerFineTuning, fetchFineTuningJobs
  } = useStore();

  const [datasetName, setDatasetName] = useState('');
  const [datasetPath, setDatasetPath] = useState('');

  // Fine-tuning form
  const [modelName, setModelName] = useState('');
  const [selectedDatasetId, setSelectedDatasetId] = useState('');
  const [epochs, setEpochs] = useState(10);
  const [lr, setLr] = useState(0.0001);

  useEffect(() => {
    if (!token) {
      router.push('/');
    } else {
      fetchDatasets();
      fetchFineTuningJobs();
    }
  }, [token]);

  const handleCreateDataset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!datasetName || !datasetPath) return;
    try {
      await createDataset(datasetName, datasetPath);
      setDatasetName('');
      setDatasetPath('');
    } catch (err) {
      console.error(err);
    }
  };

  const handleStartTraining = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modelName || !selectedDatasetId) return;
    try {
      await triggerFineTuning({
        model_name: modelName,
        dataset_id: parseInt(selectedDatasetId),
        epochs: epochs,
        learning_rate: lr
      });
      setModelName('');
      setSelectedDatasetId('');
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
              <Cpu className="w-5 h-5 text-primary" />
              MLOps & AI Model Fine-Tuning
            </h1>
            <p className="text-xs text-zinc-400">Manage image datasets, audit automatic captions, and orchestrate custom LoRA/DreamBooth runs.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 relative z-10">
        
        {/* DATASETS CONFIGS */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="glass-panel p-5 rounded-xl border border-white/5 bg-black/40">
            <h2 className="text-sm font-bold text-zinc-300 mb-4 uppercase tracking-wider flex items-center gap-1.5">
              <Database className="w-4 h-4 text-primary" /> Register Dataset
            </h2>
            <form onSubmit={handleCreateDataset} className="space-y-4">
              <div>
                <label className="text-[10px] text-zinc-400 block mb-1">Dataset Name</label>
                <input
                  type="text"
                  required
                  value={datasetName}
                  onChange={(e) => setDatasetName(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
                  placeholder="e.g. Character LoRA Set"
                />
              </div>
              <div>
                <label className="text-[10px] text-zinc-400 block mb-1">Zip Archive Path (S3/Local)</label>
                <input
                  type="text"
                  required
                  value={datasetPath}
                  onChange={(e) => setDatasetPath(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
                  placeholder="s3://datasets/character_pics.zip"
                />
              </div>
              <button
                type="submit"
                className="w-full py-2 bg-white/5 border border-white/10 hover:border-white/20 text-white font-semibold text-xs rounded-lg flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                Upload dataset registry
              </button>
            </form>
          </div>

          {/* DATASETS LIST */}
          <div className="glass-panel p-5 rounded-xl border border-white/5 bg-black/40">
            <h2 className="text-sm font-bold text-zinc-300 mb-3 uppercase tracking-wider">Validated Datasets</h2>
            {datasets.length === 0 ? (
              <span className="text-xs text-zinc-500">No datasets configured.</span>
            ) : (
              <div className="flex flex-col gap-2">
                {datasets.map(ds => (
                  <div key={ds.id} className="p-3 rounded-lg border border-white/5 bg-white/5 text-zinc-300">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-semibold">{ds.name}</span>
                      <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded ${
                        ds.status === 'VALIDATED' ? 'bg-green-950 text-green-400' : 'bg-yellow-950 text-yellow-400'
                      }`}>{ds.status}</span>
                    </div>
                    {ds.auto_captions && (
                      <div className="mt-2 text-[8px] text-zinc-500 italic truncate" title={ds.auto_captions}>
                        Caption: {JSON.parse(ds.auto_captions)["img_0.jpg"]}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* FINE-TUNING PANEL */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          <div className="grid grid-cols-1 md:grid-cols-1 gap-6">
            <div className="glass-panel p-5 rounded-xl border border-white/5 bg-black/40 flex flex-col gap-4">
              <h2 className="text-sm font-bold text-zinc-200 uppercase tracking-wider flex items-center gap-1.5">
                <PlayCircle className="w-4 h-4 text-primary" /> Orchestrate Fine-Tuning Job
              </h2>
              <form onSubmit={handleStartTraining} className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] text-zinc-400 block mb-1">Target Model Name</label>
                  <input
                    type="text"
                    required
                    value={modelName}
                    onChange={(e) => setModelName(e.target.value)}
                    className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
                    placeholder="e.g. customized-wan-astronaut"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-zinc-400 block mb-1">Select Dataset</label>
                  <select
                    value={selectedDatasetId}
                    onChange={(e) => setSelectedDatasetId(e.target.value)}
                    className="w-full bg-zinc-900 border border-white/10 text-xs text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none"
                  >
                    <option value="">-- Choose Dataset --</option>
                    {datasets.map(ds => (
                      <option key={ds.id} value={ds.id}>{ds.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] text-zinc-400 block mb-1">Training Epochs</label>
                  <input
                    type="number"
                    value={epochs}
                    onChange={(e) => setEpochs(parseInt(e.target.value))}
                    className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-zinc-400 block mb-1">Base Learning Rate</label>
                  <input
                    type="number"
                    step={0.00001}
                    value={lr}
                    onChange={(e) => setLr(parseFloat(e.target.value))}
                    className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
                  />
                </div>
                <div className="col-span-2">
                  <button
                    type="submit"
                    className="w-full py-2 bg-primary hover:bg-primary-hover font-semibold text-xs rounded-lg flex items-center justify-center gap-1.5 cursor-pointer glow-btn"
                  >
                    <Cpu className="w-3.5 h-3.5 fill-white" />
                    Trigger model fine-tuning loop
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* ACTIVE TRAINING LIST */}
          <div className="glass-panel p-5 rounded-xl border border-white/5 bg-black/40">
            <h2 className="text-sm font-bold text-zinc-300 mb-4 uppercase tracking-wider flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-secondary" /> Fine-Tuning Execution Queue
            </h2>
            {fineTuningJobs.length === 0 ? (
              <span className="text-xs text-zinc-500">Fine-tuning runs queue is currently empty.</span>
            ) : (
              <div className="flex flex-col gap-4">
                {fineTuningJobs.map(job => (
                  <div key={job.id} className="p-4 rounded-lg bg-white/5 border border-white/5 flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-zinc-300">{job.model_name} (Dataset ID: {job.dataset_id})</span>
                      <div className="flex items-center gap-2">
                        {job.status === 'RUNNING' && (
                          <span className="flex items-center gap-1 text-[10px] text-blue-400 bg-blue-950/40 border border-blue-500/25 px-2.5 py-0.5 rounded-full">
                            <RefreshCw className="w-3 h-3 animate-spin" /> Training {job.progress}%
                          </span>
                        )}
                        {job.status === 'SUCCESS' && (
                          <span className="flex items-center gap-1 text-[10px] text-green-400 bg-green-950/40 border border-green-500/25 px-2.5 py-0.5 rounded-full">
                            <CheckCircle2 className="w-3 h-3" /> Ready
                          </span>
                        )}
                        {job.status === 'FAILED' && (
                          <span className="flex items-center gap-1 text-[10px] text-red-400 bg-red-950/40 border border-red-500/25 px-2.5 py-0.5 rounded-full">
                            <AlertCircle className="w-3 h-3" /> FAILED
                          </span>
                        )}
                      </div>
                    </div>

                    {job.status === 'RUNNING' && (
                      <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-primary h-full transition-all duration-300" style={{ width: `${job.progress}%` }} />
                      </div>
                    )}

                    {job.metrics && (
                      <div className="mt-2 border-t border-white/5 pt-2">
                        <span className="text-[10px] text-zinc-400 font-bold block mb-1">Epoch Metrics Curve Logs:</span>
                        <div className="overflow-x-auto">
                          <table className="w-full text-[9px] text-zinc-500">
                            <thead>
                              <tr className="text-left border-b border-white/5">
                                <th className="pb-1">Epoch</th>
                                <th className="pb-1">Loss</th>
                                <th className="pb-1">Val Loss</th>
                                <th className="pb-1">Learning Rate</th>
                              </tr>
                            </thead>
                            <tbody>
                              {JSON.parse(job.metrics).slice(-3).map((metric: any, index: number) => (
                                <tr key={index} className="border-b border-white/5">
                                  <td className="py-1 text-zinc-400">#{metric.epoch}</td>
                                  <td className="py-1 text-red-400">{metric.loss}</td>
                                  <td className="py-1 text-orange-400">{metric.val_loss}</td>
                                  <td className="py-1">{metric.learning_rate.toExponential(3)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {job.status === 'SUCCESS' && job.result_model_path && (
                      <div className="mt-1 flex items-center gap-1 text-[10px] text-zinc-400 bg-black/40 p-2 rounded border border-white/5">
                        <Layers className="w-3.5 h-3.5 text-primary" />
                        <span>Safetensors Model Path: <span className="font-mono text-zinc-300">{job.result_model_path}</span></span>
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
