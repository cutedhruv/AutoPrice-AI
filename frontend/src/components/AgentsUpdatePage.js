import React, { useState, useEffect, useCallback } from 'react';

const API_BASE = 'http://localhost:8000';

const AGENT_META = {
  'Orchestrator': { icon: '🎯', color: 'indigo', desc: 'Coordinates the full pipeline' },
  'Market Agent': { icon: '📊', color: 'violet', desc: 'Scans competitor prices & demand' },
  'Data Agent': { icon: '💾', color: 'sky', desc: 'Gathers internal product metrics' },
  'Pricing Agent': { icon: '💰', color: 'amber', desc: 'AI/LLM pricing decision' },
  'Risk Agent': { icon: '🛡️', color: 'rose', desc: 'Validates against business rules' },
  'Execution Agent': { icon: '⚡', color: 'emerald', desc: 'Applies the approved change' },
  'Memory Agent': { icon: '🧠', color: 'purple', desc: 'Records cycle history' },
  'Admin': { icon: '👤', color: 'gray', desc: 'Manual admin action' },
};

function AgentLogTimeline({ logs }) {
  if (!logs || logs.length === 0) {
    return <p className="text-[11px] text-gray-400 italic py-2">No agent logs recorded</p>;
  }

  return (
    <div className="relative">
      {/* Vertical connector line */}
      <div className="absolute left-[13px] top-3 bottom-3 w-px bg-gray-200" />
      <div className="space-y-3">
        {logs.map((log, idx) => {
          const meta = AGENT_META[log.agent_name] || { icon: '🤖', color: 'gray', desc: '' };
          const statusConfig = {
            completed: { bg: 'bg-emerald-100', ring: 'ring-emerald-200', text: 'text-emerald-700', label: 'Done' },
            running: { bg: 'bg-amber-100', ring: 'ring-amber-200', text: 'text-amber-700', label: 'Running' },
            error: { bg: 'bg-red-100', ring: 'ring-red-200', text: 'text-red-700', label: 'Error' },
          };
          const sc = statusConfig[log.status] || statusConfig.completed;

          return (
            <div key={log.id || idx} className="relative flex items-start space-x-3 pl-0">
              <div className={`relative z-10 w-7 h-7 rounded-full flex items-center justify-center text-xs flex-shrink-0 ${sc.bg} ring-2 ${sc.ring} ring-offset-1 ring-offset-white`}>
                {meta.icon}
              </div>
              <div className="flex-1 min-w-0 bg-gray-50/60 rounded-lg px-3 py-2 border border-gray-100">
                <div className="flex items-center justify-between mb-0.5">
                  <div className="flex items-center space-x-1.5">
                    <span className="text-[11px] font-bold text-gray-800">{log.agent_name}</span>
                    <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded-full ${sc.bg} ${sc.text}`}>{sc.label}</span>
                  </div>
                  {log.timestamp && (
                    <span className="text-[9px] text-gray-400">{new Date(log.timestamp).toLocaleTimeString()}</span>
                  )}
                </div>
                <p className="text-[11px] text-gray-600 leading-snug">{log.action}</p>
                {log.details && <p className="text-[10px] text-gray-400 mt-0.5 leading-snug">{log.details}</p>}
                {meta.desc && <p className="text-[9px] text-gray-400 mt-1 italic">{meta.desc}</p>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function DecisionCard({ decision, onUndo, undoingId }) {
  const isUndoing = undoingId === decision.id;

  const typeConfig = {
    price_increase: { icon: '📈', label: 'Price Increase', tagBg: 'bg-emerald-100 text-emerald-700', accent: 'border-l-emerald-500', accentBg: 'bg-emerald-50' },
    price_decrease: { icon: '📉', label: 'Price Decrease', tagBg: 'bg-blue-100 text-blue-700', accent: 'border-l-blue-500', accentBg: 'bg-blue-50' },
    no_change: { icon: '➡️', label: 'No Change', tagBg: 'bg-gray-100 text-gray-600', accent: 'border-l-gray-300', accentBg: 'bg-gray-50' },
  };

  const config = typeConfig[decision.decision_type] || typeConfig.no_change;
  const priceChange = decision.new_price - decision.old_price;
  const changePct = decision.old_price ? ((priceChange / decision.old_price) * 100) : 0;
  const profitMargin = decision.profit_impact || 0;
  const competitorGap = decision.competitor_price
    ? (((decision.new_price - decision.competitor_price) / decision.competitor_price) * 100)
    : 0;
  const costPrice = decision.new_price && profitMargin ? decision.new_price * (1 - profitMargin / 100) : 0;

  const timeAgo = (timestamp) => {
    const diff = Date.now() - new Date(timestamp).getTime();
    const secs = Math.floor(diff / 1000);
    if (secs < 60) return 'just now';
    const mins = Math.floor(secs / 60);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    const remainMins = mins % 60;
    if (hrs < 24) return remainMins > 0 ? `${hrs}h ${remainMins}m ago` : `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
  };

  return (
    <div className={`bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden border-l-4 ${config.accent}`}>
      {/* Top bar */}
      <div className={`px-5 py-2.5 ${config.accentBg} border-b border-gray-100 flex items-center justify-between`}>
        <div className="flex items-center space-x-2 min-w-0">
          <span className="text-lg">{config.icon}</span>
          <h3 className="text-sm font-bold text-gray-900 truncate">{decision.product_name}</h3>
          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${config.tagBg}`}>{config.label}</span>
        </div>
        <div className="flex items-center space-x-2.5 flex-shrink-0">
          <div className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
            decision.confidence >= 0.8 ? 'bg-emerald-100 text-emerald-700' :
            decision.confidence >= 0.6 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'
          }`}>{(decision.confidence * 100).toFixed(0)}%</div>
          <span className="text-[10px] text-gray-400 whitespace-nowrap">{timeAgo(decision.timestamp)}</span>
        </div>
      </div>

      {/* Body — stacked layout, full width */}
      <div className="p-4 space-y-3">
        {/* Row 1: Prices + KPIs side by side */}
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Prices */}
          <div className="flex items-center gap-2 flex-1">
            <div className="flex-1 bg-gray-50 rounded-lg px-3 py-2 text-center">
              <p className="text-[8px] text-gray-400 uppercase">Previous</p>
              <p className="text-sm font-bold text-gray-400 line-through">₹{decision.old_price?.toLocaleString('en-IN')}</p>
            </div>
            <div className={`flex-1 ${config.accentBg} rounded-lg px-3 py-2 text-center`}>
              <p className="text-[8px] text-gray-500 uppercase">Current</p>
              <p className={`text-sm font-extrabold ${priceChange > 0 ? 'text-emerald-700' : priceChange < 0 ? 'text-blue-700' : 'text-gray-800'}`}>₹{decision.new_price?.toLocaleString('en-IN')}</p>
            </div>
            <div className="flex-1 bg-violet-50 rounded-lg px-3 py-2 text-center">
              <p className="text-[8px] text-violet-400 uppercase">Competitor</p>
              <p className="text-sm font-bold text-violet-700">₹{decision.competitor_price?.toLocaleString('en-IN')}</p>
            </div>
          </div>
          {/* KPIs */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <div className="bg-gray-50 rounded-lg px-3 py-2 text-center min-w-[72px]">
              <p className="text-[8px] text-gray-400 uppercase">Change</p>
              <p className={`text-xs font-bold ${priceChange > 0 ? 'text-emerald-600' : priceChange < 0 ? 'text-blue-600' : 'text-gray-500'}`}>{priceChange > 0 ? '+' : ''}{changePct.toFixed(1)}%</p>
            </div>
            <div className="bg-gray-50 rounded-lg px-3 py-2 text-center min-w-[72px]">
              <p className="text-[8px] text-gray-400 uppercase">Margin</p>
              <p className={`text-xs font-bold ${profitMargin > 20 ? 'text-emerald-600' : profitMargin > 10 ? 'text-amber-600' : 'text-red-500'}`}>{profitMargin.toFixed(1)}%</p>
            </div>
            <div className="bg-gray-50 rounded-lg px-3 py-2 text-center min-w-[72px]">
              <p className="text-[8px] text-gray-400 uppercase">vs Comp</p>
              <p className={`text-xs font-bold ${competitorGap > 0 ? 'text-red-500' : 'text-emerald-600'}`}>{competitorGap > 0 ? '+' : ''}{competitorGap.toFixed(1)}%</p>
            </div>
            <div className="bg-gray-50 rounded-lg px-3 py-2 text-center min-w-[72px]">
              <p className="text-[8px] text-gray-400 uppercase">Est. Cost</p>
              <p className="text-xs font-bold text-gray-600">₹{costPrice > 0 ? Math.round(costPrice).toLocaleString('en-IN') : '—'}</p>
            </div>
          </div>
        </div>

        {/* Row 2: Reason — full width */}
        <div className="bg-indigo-50/60 border border-indigo-100 rounded-lg p-3">
          <p className="text-[9px] text-indigo-500 uppercase font-semibold tracking-wider mb-1">AI Reasoning</p>
          <p className="text-[11px] text-gray-700 leading-relaxed">{decision.reason}</p>
        </div>

        {/* Row 3: Pipeline + Agent Trail side by side */}
        <div className="flex flex-col lg:flex-row gap-3">
          {/* Pipeline */}
          {decision.agent_chain && decision.agent_chain.length > 0 && (
            <div className="lg:w-[200px] flex-shrink-0">
              <p className="text-[9px] text-gray-400 uppercase font-semibold tracking-wider mb-1.5">Pipeline</p>
              <div className="flex lg:flex-col flex-wrap gap-1">
                {decision.agent_chain.map((agent, i) => {
                  const meta = AGENT_META[agent] || {};
                  return (
                    <div key={i} className="flex items-center space-x-1">
                      <span className="text-[9px] bg-white text-gray-600 px-1.5 py-0.5 rounded border border-gray-200 font-medium inline-flex items-center space-x-0.5">
                        <span>{meta.icon || '🤖'}</span><span>{agent}</span>
                      </span>
                      {i < decision.agent_chain.length - 1 && <span className="text-gray-300 text-[9px] lg:hidden">→</span>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Agent Trail — takes remaining width */}
          {decision.logs && decision.logs.length > 0 && (
            <div className="flex-1 border border-gray-100 rounded-lg overflow-hidden">
              <div className="bg-gray-50 px-3 py-1.5 border-b border-gray-100 flex items-center justify-between">
                <span className="text-[9px] font-bold text-gray-500 uppercase tracking-wider">🔍 Agent Trail</span>
                <span className="text-[9px] text-gray-400">{decision.logs.length} steps</span>
              </div>
              <div className="p-3 max-h-[160px] overflow-y-auto">
                <AgentLogTimeline logs={decision.logs} />
              </div>
            </div>
          )}
        </div>

        {/* Footer: ID + Undo */}
        <div className="flex items-center justify-between pt-2 border-t border-gray-100">
          <p className="text-[9px] text-gray-400">#{decision.id} &bull; {new Date(decision.timestamp).toLocaleString()}</p>
          {decision.can_undo && decision.decision_type !== 'no_change' ? (
            <button
              onClick={() => onUndo(decision.id)}
              disabled={isUndoing}
              className={`flex items-center space-x-1.5 text-[11px] font-semibold py-1.5 px-4 rounded-lg transition-all ${
                isUndoing
                  ? 'bg-gray-50 text-gray-400 cursor-not-allowed'
                  : 'bg-white border border-red-200 text-red-600 hover:bg-red-50 hover:border-red-300 shadow-sm'
              }`}
            >
              {isUndoing ? (
                <><svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg><span>Reverting...</span></>
              ) : (
                <><svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" /></svg><span>Undo</span></>
              )}
            </button>
          ) : (
            <span className="text-[9px] text-gray-300 italic">{decision.decision_type === 'no_change' ? 'No action' : 'Superseded'}</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default function AgentsUpdatePage({ onProductsRefresh }) {
  const [data, setData] = useState({ decisions: [], kpis: {} });
  const [loading, setLoading] = useState(true);
  const [undoingId, setUndoingId] = useState(null);
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchDecisionsWithLogs = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/decisions/with-logs?limit=50`);
      const json = await res.json();
      if (json.success) {
        setData(json);
      }
    } catch (e) {
      console.error('Failed to fetch decisions with logs:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDecisionsWithLogs();
    const interval = setInterval(fetchDecisionsWithLogs, 10000);
    return () => clearInterval(interval);
  }, [fetchDecisionsWithLogs]);

  const handleUndo = async (decisionId) => {
    setUndoingId(decisionId);
    try {
      const res = await fetch(`${API_BASE}/api/decisions/${decisionId}/undo`, { method: 'POST' });
      const json = await res.json();
      if (json.success) {
        await fetchDecisionsWithLogs();
        if (onProductsRefresh) onProductsRefresh();
      }
    } catch (e) {
      console.error('Failed to undo decision:', e);
    } finally {
      setUndoingId(null);
    }
  };

  const kpis = data.kpis || {};

  const filteredDecisions = (data.decisions || []).filter(d => {
    const matchesFilter = filter === 'all' || d.decision_type === filter;
    const matchesSearch = !searchQuery || d.product_name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center space-y-3">
          <svg className="w-8 h-8 animate-spin text-indigo-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span className="text-sm text-gray-400">Loading agent decisions...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-indigo-950 to-violet-950 p-8">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMSIgZmlsbD0icmdiYSgyNTUsMjU1LDI1NSwwLjAzKSIvPjwvc3ZnPg==')] opacity-50" />
        <div className="relative z-10 flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-3 mb-3">
              <div className="w-10 h-10 bg-white/10 backdrop-blur rounded-xl flex items-center justify-center">
                <span className="text-xl">🤖</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                <span className="text-emerald-300 text-xs font-medium uppercase tracking-wider">Live</span>
              </div>
            </div>
            <h1 className="text-2xl font-bold text-white mb-1">Agent Updates</h1>
            <p className="text-indigo-200 text-sm max-w-md">
              Track decisions, review reasoning, and manage pricing changes.
            </p>
          </div>
        </div>
      </div>

      {/* Toolbar: Search + Filters */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="relative flex-1 max-w-sm">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-300"
            />
          </div>
          <div className="flex items-center space-x-1">
            {[
              { id: 'all', label: 'All', count: data.decisions?.length || 0 },
              { id: 'price_increase', label: 'Increases', count: kpis.total_increases || 0 },
              { id: 'price_decrease', label: 'Decreases', count: kpis.total_decreases || 0 },
              { id: 'no_change', label: 'No Change', count: kpis.no_change_count || 0 },
            ].map(f => (
              <button
                key={f.id}
                onClick={() => setFilter(f.id)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  filter === f.id
                    ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50 border border-transparent'
                }`}
              >
                <span>{f.label}</span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                  filter === f.id ? 'bg-indigo-100 text-indigo-600' : 'bg-gray-100 text-gray-400'
                }`}>{f.count}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Decision Cards */}
      {filteredDecisions.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-12 text-center">
          <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl">🔍</span>
          </div>
          <h3 className="text-sm font-bold text-gray-700 mb-1">No decisions found</h3>
          <p className="text-xs text-gray-400">
            {searchQuery ? 'Try a different search term' : 'Waiting for the agent to make pricing decisions...'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredDecisions.map(decision => (
            <DecisionCard
              key={decision.id}
              decision={decision}
              onUndo={handleUndo}
              undoingId={undoingId}
            />
          ))}
        </div>
      )}
    </div>
  );
}
