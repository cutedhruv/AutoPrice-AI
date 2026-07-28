import React from 'react';

export default function TopNavBar({
  isConnected,
  agentRunning,
  lastUpdatedAt,
  activeTab,
  onTabChange,
  isDark,
  onToggleTheme,
}) {
  const navTabs = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'demo', label: 'Live Demo' },
    { id: 'updates', label: 'Agent Updates' },
    { id: 'products', label: 'Products' },
    { id: 'analytics', label: 'Analytics' },
  ];

  return (
    <header className={`sticky top-0 z-40 border-b backdrop-blur ${
      isDark
        ? 'border-slate-700 bg-slate-900/95'
        : 'border-slate-200 bg-white/95'
    }`}>
      <div className="max-w-[1600px] mx-auto px-5 py-3 flex flex-col gap-3">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className={`text-[11px] uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>AutoPrice AI</p>
            <h1 className={`text-xl font-semibold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>Autonomous Pricing Analyst Agent</h1>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span
              className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-full border ${
                isConnected
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-slate-50 text-slate-600 border-slate-200'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'
                }`}
              />
              {agentRunning ? 'System Running' : 'Idle'}
            </span>
            <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>
              Last update: {lastUpdatedAt ? new Date(lastUpdatedAt).toLocaleTimeString() : '--'}
            </span>
            <button
              onClick={onToggleTheme}
              className={`px-2.5 py-1 rounded-lg border text-xs font-medium ${
                isDark
                  ? 'bg-slate-800 text-slate-200 border-slate-700 hover:bg-slate-700'
                  : 'bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200'
              }`}
            >
              {isDark ? 'Light Mode' : 'Dark Mode'}
            </button>
          </div>
        </div>

        <nav className="flex gap-2 overflow-x-auto">
          {navTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : isDark
                    ? 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
    </header>
  );
}

