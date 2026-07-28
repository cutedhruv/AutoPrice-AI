import React from 'react';

export default function Header({ isConnected, stats }) {
  return (
    <header className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 bg-gradient-to-br from-violet-500 to-indigo-500 rounded-xl flex items-center justify-center shadow-lg shadow-violet-500/20">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">AutoPrice AI</h1>
              <p className="text-[11px] text-indigo-300 -mt-0.5">Autonomous Pricing Intelligence</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Agent Status */}
            <div className="hidden sm:flex items-center space-x-2 bg-white/5 border border-white/10 rounded-full px-3 py-1.5">
              <div className={`w-2 h-2 rounded-full ${
                stats?.agent_running 
                  ? 'bg-emerald-400 animate-pulse' 
                  : 'bg-yellow-400'
              }`} />
              <span className="text-xs font-medium text-white/80">
                {stats?.agent_running ? 'Agent Active' : 'Idle'}
              </span>
            </div>

            {/* Connection */}
            <div className="flex items-center space-x-1.5 bg-white/5 border border-white/10 rounded-full px-3 py-1.5">
              <div className={`w-1.5 h-1.5 rounded-full ${
                isConnected ? 'bg-emerald-400' : 'bg-red-400'
              }`} />
              <span className="text-[11px] text-white/70">
                {isConnected ? 'Connected' : 'Offline'}
              </span>
            </div>

            {/* Cycles */}
            <div className="hidden md:flex items-center space-x-2 bg-white/5 border border-white/10 rounded-full px-3 py-1.5">
              <span className="text-[11px] text-white/50">Cycles</span>
              <span className="text-sm font-bold text-white">{stats?.total_cycles || 0}</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
