import React from 'react';

export default function DecisionLog({ decisions }) {
  const decisionIcons = {
    'price_increase': '📈',
    'price_decrease': '📉',
    'no_change': '➡️'
  };

  const decisionColors = {
    'price_increase': 'bg-green-50 border-green-200',
    'price_decrease': 'bg-blue-50 border-blue-200',
    'no_change': 'bg-gray-50 border-gray-200'
  };

  const timeAgo = (timestamp) => {
    const diff = Date.now() - new Date(timestamp).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 className="text-sm font-bold text-gray-800">Recent Decisions</h3>
        <span className="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full font-medium">{decisions.length} total</span>
      </div>

      {decisions.length === 0 ? (
        <div className="p-8 text-center">
          <p className="text-xs text-gray-400">No decisions recorded yet.</p>
        </div>
      ) : (
        <div className="p-4 space-y-3 max-h-[400px] overflow-y-auto">
          {decisions.slice(0, 10).map((decision, idx) => (
            <div
              key={decision.id || idx}
              className={`${decisionColors[decision.decision_type] || 'bg-white'} border rounded-xl p-4 animate-fade-in`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{decisionIcons[decision.decision_type] || '🔄'}</span>
                  <div>
                    <h4 className="text-sm font-semibold text-gray-800">{decision.product_name}</h4>
                    <p className="text-xs text-gray-500 capitalize">
                      {decision.decision_type?.replace('_', ' ')}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-400">{timeAgo(decision.timestamp)}</p>
                  <div className="flex items-center mt-1 space-x-1">
                    <span className="text-xs text-gray-500">Confidence:</span>
                    <span className="text-xs font-medium text-primary-600">
                      {(decision.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Price Change */}
              <div className="mt-3 flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-500">Old:</span>
                  <span className="text-sm font-medium text-gray-700">
                    ₹{decision.old_price?.toLocaleString('en-IN')}
                  </span>
                </div>
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-500">New:</span>
                  <span className={`text-sm font-bold ${
                    decision.new_price > decision.old_price ? 'text-green-600' : 
                    decision.new_price < decision.old_price ? 'text-blue-600' : 'text-gray-600'
                  }`}>
                    ₹{decision.new_price?.toLocaleString('en-IN')}
                  </span>
                </div>
                <span className="text-xs text-gray-400 ml-auto">
                  vs Competitor: ₹{decision.competitor_price?.toLocaleString('en-IN')}
                </span>
              </div>

              {/* Reason */}
              <div className="mt-3 bg-white/60 rounded-lg p-3">
                <p className="text-xs text-gray-600 leading-relaxed">{decision.reason}</p>
              </div>

              {/* Agent Chain */}
              {decision.agent_chain && decision.agent_chain.length > 0 && (
                <div className="mt-2 flex items-center space-x-1">
                  <span className="text-xs text-gray-400">Pipeline:</span>
                  {decision.agent_chain.map((agent, i) => (
                    <span key={i} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                      {agent}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
