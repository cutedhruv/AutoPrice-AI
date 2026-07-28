import React from 'react';

function AgentStatusItem({ item }) {
  const statusColors = {
    running: 'border-l-yellow-400 bg-yellow-50',
    completed: 'border-l-green-400 bg-green-50',
    error: 'border-l-red-400 bg-red-50'
  };

  const agentIcons = {
    'Orchestrator': '🎯',
    'Market Agent': '📊',
    'Data Agent': '💾',
    'Pricing Agent': '💰',
    'Risk Agent': '🛡️',
    'Execution Agent': '⚡',
    'Memory Agent': '🧠'
  };

  return (
    <div className={`border-l-4 ${statusColors[item.status] || 'border-l-gray-300 bg-gray-50'} p-3 rounded-r-lg animate-fade-in`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-sm">{agentIcons[item.agent] || '🤖'}</span>
          <span className="text-xs font-semibold text-gray-800">{item.agent}</span>
          <span className={`activity-dot ${item.status}`} />
        </div>
        {item.product_id && (
          <span className="text-xs text-gray-400">#{item.product_id}</span>
        )}
      </div>
      <p className="text-xs text-gray-600 mt-1 truncate">{item.step}</p>
    </div>
  );
}

function ActivityLogItem({ item }) {
  const statusColors = {
    running: 'text-yellow-600',
    completed: 'text-green-600',
    error: 'text-red-600'
  };

  const timeAgo = (timestamp) => {
    const diff = Date.now() - new Date(timestamp).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    return `${hrs}h ago`;
  };

  return (
    <div className="flex items-start space-x-3 py-2 border-b border-gray-50 last:border-0">
      <div className={`activity-dot ${item.status} mt-1.5`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-gray-700">{item.agent_name}</span>
          <span className="text-xs text-gray-400">{timeAgo(item.timestamp)}</span>
        </div>
        <p className="text-xs text-gray-500 truncate">{item.action}</p>
      </div>
    </div>
  );
}

export default function AgentActivityPanel({ activity, liveActivity, fullView }) {
  const liveItems = activity || [];
  const historyItems = liveActivity || [];

  if (fullView) {
    return (
      <div className="space-y-6">
        {/* Live Agent Status */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="p-4 border-b border-gray-100">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <h3 className="text-sm font-bold text-gray-800">Live Agent Status</h3>
            </div>
          </div>
          <div className="p-4 space-y-2 max-h-96 overflow-y-auto">
            {liveItems.length === 0 ? (
              <p className="text-xs text-gray-400 text-center py-4">Waiting for agent activity...</p>
            ) : (
              liveItems.map((item, idx) => <AgentStatusItem key={idx} item={item} />)
            )}
          </div>
        </div>

        {/* Activity History */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="p-4 border-b border-gray-100">
            <h3 className="text-sm font-bold text-gray-800">Activity History</h3>
          </div>
          <div className="p-4 max-h-[600px] overflow-y-auto">
            {historyItems.length === 0 ? (
              <p className="text-xs text-gray-400 text-center py-4">No activity recorded yet</p>
            ) : (
              historyItems.map((item, idx) => <ActivityLogItem key={idx} item={item} />)
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
            <h3 className="text-sm font-bold text-gray-800">Agent Activity</h3>
          </div>
          <span className="text-[10px] uppercase tracking-wider text-gray-400 font-medium">Live</span>
        </div>
      </div>
      <div className="p-3 space-y-2 max-h-80 overflow-y-auto">
        {liveItems.length === 0 ? (
          <p className="text-xs text-gray-400 text-center py-4">Waiting for agent activity...</p>
        ) : (
          liveItems.slice(0, 8).map((item, idx) => <AgentStatusItem key={idx} item={item} />)
        )}
      </div>
    </div>
  );
}
