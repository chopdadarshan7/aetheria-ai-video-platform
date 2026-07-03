/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useStore, Team, ApiKey, CreditTransaction } from '../store';
import { 
  ArrowLeft, CreditCard, Users, ShieldAlert, Sparkles, Plus, Key,
  CheckCircle2, Coins, ArrowUpRight, ArrowDownRight, Globe
} from 'lucide-react';
import Link from 'next/link';

export default function SaaSControlPanel() {
  const router = useRouter();
  const {
    token, user, teams, apiKeys, creditTransactions, loading,
    fetchUser, fetchTeams, createTeam, fetchApiKeys, createApiKey,
    fetchBillingTransactions, checkoutPlan, triggerWebhookDeposit
  } = useStore();

  const [teamName, setTeamName] = useState('');
  const [keyName, setKeyName] = useState('');
  const [paymentSuccess, setPaymentSuccess] = useState(false);

  useEffect(() => {
    if (!token) {
      router.push('/');
    } else {
      fetchUser();
      fetchTeams();
      fetchApiKeys();
      fetchBillingTransactions();

      // Check payment params
      const params = new URLSearchParams(window.location.search);
      if (params.get('payment_success') === 'true') {
        setPaymentSuccess(true);
      }
    }
  }, [token]);

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!teamName) return;
    try {
      await createTeam(teamName);
      setTeamName('');
    } catch (err) {
      console.error(err);
    }
  };

  const handleGenerateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyName) return;
    try {
      await createApiKey(keyName);
      setKeyName('');
    } catch (err) {
      console.error(err);
    }
  };

  const handleCheckout = async (plan: string) => {
    try {
      const url = await checkoutPlan(plan);
      window.location.href = url;
    } catch (err) {
      console.error(err);
    }
  };

  const handleDepositMock = async () => {
    // Inject 500 mock tokens via Stripe simulated webhook
    await triggerWebhookDeposit(500);
  };

  return (
    <div className="flex-1 min-h-screen bg-background text-white p-6 relative">
      <div className="absolute top-10 left-1/3 glowing-orb bg-secondary/10" />

      {/* TOP HEADER */}
      <div className="flex items-center justify-between mb-8 relative z-10 border-b border-white/5 pb-4">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="p-2 hover:bg-white/5 rounded-lg border border-white/5 text-zinc-300 transition">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-wide flex items-center gap-2">
              <CreditCard className="w-5 h-5 text-secondary" />
              Enterprise Billing & Workspaces
            </h1>
            <p className="text-xs text-zinc-400">Configure corporate teams workspaces, purchase API keys, and manage token balances.</p>
          </div>
        </div>
      </div>

      {paymentSuccess && (
        <div className="mb-6 p-4 rounded-xl border border-green-500/25 bg-green-950/40 text-green-400 text-xs flex items-center gap-2 relative z-10">
          <CheckCircle2 className="w-4 h-4" />
          <span>Payment checkout completed successfully! Cloned plan has been applied to your account.</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 relative z-10">
        
        {/* SUBSCRIPTION PLANS & BALANCES */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* TOKEN LEDGER */}
            <div className="glass-panel p-6 rounded-xl border border-white/5 bg-black/40 flex flex-col justify-between">
              <div className="space-y-4">
                <span className="text-xs text-zinc-400 uppercase font-bold tracking-wider flex items-center gap-1.5">
                  <Coins className="w-4 h-4 text-secondary" /> Active Token Balance
                </span>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-extrabold tracking-tight text-white">{user?.credits || 0}</span>
                  <span className="text-xs text-zinc-500">Credits</span>
                </div>
                <p className="text-[10px] text-zinc-400">Tokens are consumed dynamically per second of generated video/audio content.</p>
              </div>
              <button
                onClick={handleDepositMock}
                className="mt-6 w-full py-2 bg-secondary hover:bg-secondary-hover font-semibold text-xs rounded-lg flex items-center justify-center gap-1.5 cursor-pointer glow-btn"
              >
                <Plus className="w-3.5 h-3.5 fill-white" />
                Buy 500 Credits (Stripe simulation webhook)
              </button>
            </div>

            {/* PLANS GRID */}
            <div className="glass-panel p-6 rounded-xl border border-white/5 bg-black/40 flex flex-col justify-between">
              <div className="space-y-3">
                <span className="text-xs text-zinc-400 uppercase font-bold tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-primary" /> Subscription Tiers
                </span>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center bg-white/5 p-2 rounded">
                    <span className="font-semibold text-zinc-300">Creator Tier ($30/mo)</span>
                    <button 
                      onClick={() => handleCheckout('creator')}
                      className="px-3 py-1 bg-white/5 hover:bg-white/10 rounded text-[10px] border border-white/10"
                    >
                      Subscribe
                    </button>
                  </div>
                  <div className="flex justify-between items-center bg-white/5 p-2 rounded">
                    <span className="font-semibold text-zinc-300">Enterprise Tier ($120/mo)</span>
                    <button 
                      onClick={() => handleCheckout('enterprise')}
                      className="px-3 py-1 bg-white/5 hover:bg-white/10 rounded text-[10px] border border-white/10"
                    >
                      Subscribe
                    </button>
                  </div>
                </div>
              </div>
            </div>

          </div>

          {/* LEDGER LOGS TABLE */}
          <div className="glass-panel p-5 rounded-xl border border-white/5 bg-black/40">
            <h2 className="text-sm font-bold text-zinc-300 mb-4 uppercase tracking-wider">Credits Transaction Ledger</h2>
            {creditTransactions.length === 0 ? (
              <span className="text-xs text-zinc-500">No transaction logs logged.</span>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-zinc-500">
                  <thead>
                    <tr className="text-left border-b border-white/5 pb-2 text-[10px] uppercase text-zinc-400">
                      <th className="pb-2">Transaction ID</th>
                      <th className="pb-2">Type</th>
                      <th className="pb-2">Details</th>
                      <th className="pb-2">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {creditTransactions.map(tx => (
                      <tr key={tx.id} className="border-b border-white/5">
                        <td className="py-2.5 text-zinc-400 font-mono text-[10px]">#{tx.id}</td>
                        <td className="py-2.5 capitalize">{tx.transaction_type}</td>
                        <td className="py-2.5 italic">{tx.description || 'System account adjust'}</td>
                        <td className="py-2.5 font-bold">
                          {tx.amount > 0 ? (
                            <span className="text-green-400 flex items-center gap-0.5"><ArrowUpRight className="w-3.5 h-3.5" /> +{tx.amount}</span>
                          ) : (
                            <span className="text-red-400 flex items-center gap-0.5"><ArrowDownRight className="w-3.5 h-3.5" /> {tx.amount}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* WORKSPACES & API KEYS */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          
          {/* TEAMS */}
          <div className="glass-panel p-5 rounded-xl border border-white/5 bg-black/40">
            <h2 className="text-sm font-bold text-zinc-300 mb-4 uppercase tracking-wider flex items-center gap-1.5">
              <Users className="w-4 h-4 text-primary" /> Teams Workspaces
            </h2>
            <form onSubmit={handleCreateTeam} className="space-y-3 mb-4">
              <input
                type="text"
                required
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
                placeholder="Team Name (e.g. Design Agency)"
              />
              <button
                type="submit"
                className="w-full py-1.5 bg-white/5 border border-white/10 hover:border-white/20 text-xs font-semibold rounded-lg flex items-center justify-center gap-1 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" /> Initialize Team
              </button>
            </form>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {teams.length === 0 ? (
                <span className="text-[10px] text-zinc-500">No team workspaces created.</span>
              ) : (
                teams.map(t => (
                  <div key={t.id} className="p-2.5 rounded bg-white/5 border border-white/5 text-xs text-zinc-300 font-semibold truncate">
                    {t.name}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* API KEYS */}
          <div className="glass-panel p-5 rounded-xl border border-white/5 bg-black/40">
            <h2 className="text-sm font-bold text-zinc-300 mb-4 uppercase tracking-wider flex items-center gap-1.5">
              <Key className="w-4 h-4 text-secondary" /> Api Keys Management
            </h2>
            <form onSubmit={handleGenerateKey} className="space-y-3 mb-4">
              <input
                type="text"
                required
                value={keyName}
                onChange={(e) => setKeyName(e.target.value)}
                className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
                placeholder="Key Description (e.g. CLI Deploy)"
              />
              <button
                type="submit"
                className="w-full py-1.5 bg-white/5 border border-white/10 hover:border-white/20 text-xs font-semibold rounded-lg flex items-center justify-center gap-1 cursor-pointer"
              >
                <Globe className="w-3.5 h-3.5 text-secondary" /> Generate API Key
              </button>
            </form>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {apiKeys.length === 0 ? (
                <span className="text-[10px] text-zinc-500">No api keys configured.</span>
              ) : (
                apiKeys.map(key => (
                  <div key={key.id} className="p-2.5 rounded bg-white/5 border border-white/5 flex flex-col gap-1 text-[10px]">
                    <span className="font-bold text-zinc-300">{key.name}</span>
                    <span className="font-mono text-zinc-500 select-all truncate">{key.key_hash}</span>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
