import React, { useMemo, useState } from 'react';

const API_BASE = 'http://localhost:8000';

function inr(value) {
  if (value === undefined || value === null) return '-';
  return `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
}

function timeAgo(ts) {
  const diff = Date.now() - new Date(ts).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function AgentUpdatesPage({ updates, onRefresh }) {
  const [undoLoadingId, setUndoLoadingId] = useState(null);
  const orderedUpdates = useMemo(() => updates || [], [updates]);

  const handleUndo = async (update) => {
    const confirmed = window.confirm(
      `Undo price update for ${update.product_name}?\n${inr(update.new_price)} -> ${inr(update.old_price)}`
    );
    if (!confirmed) return;

    try {
      setUndoLoadingId(update.id);
      const res = await fetch(`${API_BASE}/api/updates/${update.id}/undo`, {
        method: 'POST',
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        alert(data?.detail?.message || data?.detail || data?.message || 'Undo failed');
        return;
      }
      await onRefresh?.();
    } catch (e) {
      alert(`Undo failed: ${e.message}`);
    } finally {
      setUndoLoadingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-6 text-white">
        <h2 className="text-xl font-bold">Agent Price Updates</h2>
        <p className="text-sm text-indigo-100 mt-1">
          Full explainable feed of recent AI decisions, metrics, and pipeline analysis. You can undo any
          update if the result does not fit your business preference.
        </p>
      </div>

      {orderedUpdates.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 p-10 text-center text-gray-500">
          No updates yet. Trigger a competitor change in Live Demo to see explainable cards here.
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {orderedUpdates.map((u) => {
            const isIncrease = (u.metrics?.delta || 0) > 0;
            const isUndo = u.decision_type === 'manual_undo';
            return (
              <div key={u.id} className="bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-100 flex items-start justify-between">
                  <div>
                    <p className="text-sm font-bold text-gray-900">{u.product_name}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {u.decision_type?.replace('_', ' ')} • {timeAgo(u.timestamp)}
                    </p>
                  </div>
                  <span
                    className={`text-xs px-2 py-1 rounded-full font-semibold ${
                      isUndo
                        ? 'bg-amber-100 text-amber-700'
                        : isIncrease
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-blue-100 text-blue-700'
                    }`}
                  >
                    {isUndo ? 'Manual Undo' : isIncrease ? 'Increase' : 'Decrease'}
                  </span>
                </div>

                <div className="p-5 space-y-4">
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-gray-50 rounded-xl p-3">
                      <p className="text-[10px] uppercase text-gray-500 font-semibold">Old</p>
                      <p className="text-sm font-bold text-gray-800">{inr(u.old_price)}</p>
                    </div>
                    <div className="bg-indigo-50 rounded-xl p-3">
                      <p className="text-[10px] uppercase text-indigo-500 font-semibold">New</p>
                      <p className="text-sm font-bold text-indigo-700">{inr(u.new_price)}</p>
                    </div>
                    <div className="bg-slate-50 rounded-xl p-3">
                      <p className="text-[10px] uppercase text-slate-500 font-semibold">Delta</p>
                      <p className={`text-sm font-bold ${(u.metrics?.delta || 0) >= 0 ? 'text-emerald-600' : 'text-blue-600'}`}>
                        {inr(u.metrics?.delta)} ({(u.metrics?.delta_pct || 0) > 0 ? '+' : ''}
                        {(u.metrics?.delta_pct || 0).toFixed(2)}%)
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-gray-50 rounded-xl p-3">
                      <p className="text-[10px] uppercase text-gray-500 font-semibold">Competitor</p>
                      <p className="text-sm font-semibold text-gray-700">{inr(u.competitor_price)}</p>
                    </div>
                    <div className="bg-gray-50 rounded-xl p-3">
                      <p className="text-[10px] uppercase text-gray-500 font-semibold">Confidence / Margin</p>
                      <p className="text-sm font-semibold text-gray-700">
                        {(u.confidence * 100).toFixed(0)}% / {(u.metrics?.profit_margin_after ?? 0).toFixed(2)}%
                      </p>
                    </div>
                  </div>

                  <div className="bg-indigo-50/60 rounded-xl p-3 border border-indigo-100">
                    <p className="text-[11px] font-semibold text-indigo-700 uppercase tracking-wide mb-1">
                      Why agent updated price
                    </p>
                    <p className="text-sm text-gray-700 leading-relaxed">{u.reason}</p>
                  </div>

                  <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
                    <p className="text-[11px] font-semibold text-slate-700 uppercase tracking-wide mb-2">
                      Research and Analysis Timeline
                    </p>
                    <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                      {(u.analysis_logs || []).length === 0 ? (
                        <p className="text-xs text-gray-500">No detailed logs captured for this update.</p>
                      ) : (
                        u.analysis_logs.map((log, idx) => (
                          <div key={`${u.id}-${idx}`} className="text-xs">
                            <p className="font-semibold text-gray-700">
                              {log.agent_name} • {log.action}
                            </p>
                            <p className="text-gray-600">{log.details}</p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between gap-3 pt-1">
                    <div className="flex flex-wrap gap-2">
                      {(u.agent_chain || []).map((a, i) => (
                        <span key={`${u.id}-agent-${i}`} className="text-[11px] bg-gray-100 text-gray-600 px-2 py-1 rounded-md">
                          {a}
                        </span>
                      ))}
                    </div>
                    {!isUndo && (
                      <button
                        onClick={() => handleUndo(u)}
                        disabled={undoLoadingId === u.id}
                        className="text-xs font-semibold px-3 py-2 rounded-lg bg-rose-600 hover:bg-rose-700 text-white disabled:opacity-60"
                      >
                        {undoLoadingId === u.id ? 'Undoing...' : 'Undo Update'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
