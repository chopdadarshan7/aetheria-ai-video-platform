/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import React, { useState } from 'react';
import { useStore } from '../store';
import { Sparkles, Mail, Lock, User, Loader2 } from 'lucide-react';

interface AuthCardProps {
  onSuccess: () => void;
}

export default function AuthCard({ onSuccess }: AuthCardProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const setToken = useStore((state) => state.setToken);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setLoading(true);

    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

    try {
      if (isLogin) {
        // OAuth2 Password Grant requires application/x-www-form-urlencoded
        const body = new URLSearchParams();
        body.append('username', username);
        body.append('password', password);

        const res = await fetch(`${API_BASE_URL}/auth/token`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: body.toString(),
        });

        if (!res.ok) {
          throw new Error('Invalid username or password');
        }

        const data = await res.json();
        setToken(data.access_token);
        onSuccess();
      } else {
        const res = await fetch(`${API_BASE_URL}/auth/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ username, email, password }),
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData?.detail || 'Registration failed');
        }

        // Auto login on successful registration
        const body = new URLSearchParams();
        body.append('username', username);
        body.append('password', password);
        
        const loginResJson = await fetch(`${API_BASE_URL}/auth/token`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: body.toString()
        });

        if (!loginResJson.ok) {
          throw new Error('Auto-login failed after registration');
        }

        const data = await loginResJson.json();
        setToken(data.access_token);
        onSuccess();
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Authentication error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md p-8 rounded-2xl glass-panel relative overflow-hidden">
      {/* Decorative colored glow inside the card */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-primary/20 rounded-full filter blur-2xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-32 h-32 bg-secondary/20 rounded-full filter blur-2xl pointer-events-none" />

      <div className="flex flex-col items-center mb-8 relative z-10">
        <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-3 border border-primary/20">
          <Sparkles className="w-6 h-6 text-primary glow-text" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          {isLogin ? 'Welcome Back' : 'Create Account'}
        </h2>
        <p className="text-zinc-400 text-sm mt-1">
          {isLogin ? 'Sign in to access your video workstation' : 'Sign up to start generating with AI'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 relative z-10">
        <div>
          <label className="block text-zinc-300 text-sm font-medium mb-1.5" htmlFor="username">
            Username
          </label>
          <div className="relative">
            <User className="absolute left-3.5 top-3 w-5 h-5 text-zinc-500" />
            <input
              id="username"
              type="text"
              required
              className="w-full pl-11 pr-4 py-2.5 rounded-lg glass-input text-sm"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
        </div>

        {!isLogin && (
          <div>
            <label className="block text-zinc-300 text-sm font-medium mb-1.5" htmlFor="email">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-3 w-5 h-5 text-zinc-500" />
              <input
                id="email"
                type="email"
                required
                className="w-full pl-11 pr-4 py-2.5 rounded-lg glass-input text-sm"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>
        )}

        <div>
          <label className="block text-zinc-300 text-sm font-medium mb-1.5" htmlFor="password">
            Password
          </label>
          <div className="relative">
            <Lock className="absolute left-3.5 top-3 w-5 h-5 text-zinc-500" />
            <input
              id="password"
              type="password"
              required
              className="w-full pl-11 pr-4 py-2.5 rounded-lg glass-input text-sm"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
        </div>

        {errorMsg && (
          <div className="p-3 bg-red-950/40 border border-red-500/30 rounded-lg text-red-400 text-xs">
            {errorMsg}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 rounded-lg text-white font-medium text-sm glow-btn cursor-pointer flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Processing...
            </>
          ) : isLogin ? (
            'Sign In'
          ) : (
            'Get Started'
          )}
        </button>
      </form>

      <div className="mt-6 text-center text-sm text-zinc-400 relative z-10">
        {isLogin ? (
          <p>
            Don&apos;t have an account?{' '}
            <button
              onClick={() => {
                setIsLogin(false);
                setErrorMsg('');
              }}
              className="text-primary hover:underline font-medium cursor-pointer"
            >
              Sign Up
            </button>
          </p>
        ) : (
          <p>
            Already have an account?{' '}
            <button
              onClick={() => {
                setIsLogin(true);
                setErrorMsg('');
              }}
              className="text-primary hover:underline font-medium cursor-pointer"
            >
              Sign In
            </button>
          </p>
        )}
      </div>
    </div>
  );
}
