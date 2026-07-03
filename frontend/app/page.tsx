'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useStore } from './store';
import AuthCard from './components/AuthCard';
import { Sparkles, Cpu, Zap } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const token = useStore((state) => state.token);

  useEffect(() => {
    if (token) {
      router.push('/dashboard');
    }
  }, [token, router]);

  const handleAuthSuccess = () => {
    router.push('/dashboard');
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 relative overflow-hidden bg-[#09090b]">
      {/* Dynamic background glowing shapes */}
      <div className="absolute top-10 left-10 glowing-orb bg-primary/20" />
      <div className="absolute bottom-10 right-10 glowing-orb bg-secondary/20" />

      {/* Main Container */}
      <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-12 gap-12 items-center relative z-10">
        
        {/* HERO BRANDING DESCRIPTION */}
        <div className="lg:col-span-7 flex flex-col gap-6 text-left">
          <div className="inline-flex items-center gap-2 bg-primary/10 border border-primary/20 px-3 py-1.5 rounded-full w-fit">
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-xs font-semibold text-primary">Generative Video Engine V1.0</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
            The Future of <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">Generative Cinema</span>
          </h1>

          <p className="text-zinc-400 text-lg leading-relaxed max-w-xl">
            Aetheria AI simplifies video creation. Instantly transform textual descriptions, images, or source videos into high-fidelity cinematic productions using our advanced decentralized GPU render pipeline.
          </p>

          {/* Key Platform Highlights */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
            <div className="flex items-center gap-3 bg-white/5 border border-white/5 p-3 rounded-xl">
              <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center border border-primary/20">
                <Cpu className="w-5 h-5 text-primary" />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-white">Wan & CogVideoX</span>
                <span className="text-[10px] text-zinc-500">Industry-leading diffusion models</span>
              </div>
            </div>

            <div className="flex items-center gap-3 bg-white/5 border border-white/5 p-3 rounded-xl">
              <div className="w-10 h-10 bg-secondary/10 rounded-lg flex items-center justify-center border border-secondary/20">
                <Zap className="w-5 h-5 text-secondary" />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-white">Distributed Queue</span>
                <span className="text-[10px] text-zinc-500">Simultaneous rendering task clusters</span>
              </div>
            </div>
          </div>
        </div>

        {/* GLASSMORPHIC AUTHENTICATION PORTAL */}
        <div className="lg:col-span-5 flex items-center justify-center">
          <AuthCard onSuccess={handleAuthSuccess} />
        </div>
      </div>
    </div>
  );
}
