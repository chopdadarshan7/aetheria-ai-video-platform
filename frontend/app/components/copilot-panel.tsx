/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import React, { useState } from 'react';
import { useStore } from '../store';
import { 
  Sparkles, MessageSquare, Send, X, Calculator, Cpu, Coins, Clock
} from 'lucide-react';

export default function CopilotPanel() {
  const { copilotMessages, sendCopilotMessage, estimateRenderCost } = useStore();
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  
  // Cost estimator state
  const [duration, setDuration] = useState(5);
  const [steps, setSteps] = useState(25);
  const [estimate, setEstimate] = useState<any>(null);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    const msg = input;
    setInput('');
    await sendCopilotMessage(msg);
  };

  const handleCalculate = async () => {
    try {
      const result = await estimateRenderCost(duration, steps);
      setEstimate(result);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <>
      {/* FLOATING TRIGGERS */}
      <button 
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-40 p-4 bg-primary hover:bg-primary-hover text-white rounded-full shadow-2xl transition flex items-center gap-2 cursor-pointer glow-btn font-semibold text-xs"
      >
        <Sparkles className="w-4 h-4 text-white" />
        Ask AI Copilot
      </button>

      {/* SIDE DRAWER */}
      <div className={`fixed top-0 right-0 h-full w-80 md:w-96 z-50 glass-panel border-l border-white/10 bg-zinc-950/95 shadow-2xl transition-transform duration-300 transform ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      } flex flex-col justify-between p-5`}>
        
        {/* HEADER */}
        <div className="flex justify-between items-center border-b border-white/5 pb-3">
          <span className="text-sm font-bold tracking-wide flex items-center gap-1.5 text-zinc-200">
            <Sparkles className="w-4.5 h-4.5 text-primary" /> AI Copilot Assistant
          </span>
          <button 
            onClick={() => setIsOpen(false)}
            className="p-1 hover:bg-white/5 rounded text-zinc-500 hover:text-white transition"
          >
            <X className="w-4.5 h-4.5" />
          </button>
        </div>

        {/* CHAT BUBBLES SCROLL AREA */}
        <div className="flex-1 overflow-y-auto my-4 space-y-3.5 pr-1">
          {copilotMessages.map((msg, i) => (
            <div 
              key={i} 
              className={`p-3 rounded-lg text-xs leading-relaxed max-w-[85%] ${
                msg.role === 'user' 
                  ? 'bg-primary/20 border border-primary/25 text-white ml-auto' 
                  : 'bg-white/5 border border-white/5 text-zinc-300 mr-auto'
              }`}
            >
              <div className="flex items-center gap-1 mb-1 text-[9px] text-zinc-500 font-bold uppercase">
                <MessageSquare className="w-3 h-3" />
                {msg.role === 'user' ? 'You' : 'Copilot'}
              </div>
              <p className="whitespace-pre-line">{msg.text}</p>
            </div>
          ))}
        </div>

        {/* COST ESTIMATION CARD */}
        <div className="bg-black/40 border border-white/5 p-3 rounded-lg mb-4 space-y-2">
          <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
            <Calculator className="w-3.5 h-3.5 text-secondary" /> GPU VRAM Cost Estimator
          </span>
          <div className="grid grid-cols-2 gap-2.5 text-[10px]">
            <div>
              <label className="text-zinc-500 block mb-0.5">Duration (s)</label>
              <input 
                type="number" 
                value={duration} 
                onChange={(e) => setDuration(parseFloat(e.target.value))} 
                className="w-full bg-zinc-900 border border-white/10 px-2 py-1 rounded text-zinc-300 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-zinc-500 block mb-0.5">Steps</label>
              <input 
                type="number" 
                value={steps} 
                onChange={(e) => setSteps(parseInt(e.target.value))} 
                className="w-full bg-zinc-900 border border-white/10 px-2 py-1 rounded text-zinc-300 focus:outline-none"
              />
            </div>
          </div>
          <button 
            onClick={handleCalculate}
            className="w-full py-1 bg-white/5 hover:bg-white/10 text-white font-semibold text-[10px] rounded border border-white/10"
          >
            Compute Estimate
          </button>
          
          {estimate && (
            <div className="grid grid-cols-3 gap-1.5 pt-2 text-[9px] border-t border-white/5 text-zinc-400">
              <div className="flex flex-col items-center p-1 bg-zinc-900 rounded">
                <Clock className="w-3 h-3 text-secondary mb-0.5" />
                <span>{estimate.estimated_vram_time_seconds}s GPU</span>
              </div>
              <div className="flex flex-col items-center p-1 bg-zinc-900 rounded">
                <Coins className="w-3 h-3 text-primary mb-0.5" />
                <span>{estimate.credits_cost} Credits</span>
              </div>
              <div className="flex flex-col items-center p-1 bg-zinc-900 rounded">
                <Cpu className="w-3 h-3 text-green-400 mb-0.5" />
                <span>{estimate.gpu_vram_required_gb}GB VRAM</span>
              </div>
            </div>
          )}
        </div>

        {/* INPUT INPUT */}
        <form onSubmit={handleSend} className="flex gap-2">
          <input 
            type="text"
            required
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask copilot: Pan shot camera..."
            className="flex-1 px-3 py-2 rounded-lg glass-input text-xs"
          />
          <button 
            type="submit"
            className="p-2.5 bg-primary hover:bg-primary-hover text-white rounded-lg transition"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>

      </div>
    </>
  );
}
