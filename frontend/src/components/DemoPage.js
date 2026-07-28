import React, { useState, useEffect, useRef } from 'react';

const API_BASE = 'http://localhost:8000';

export default function DemoPage({ products, onProductsRefresh }) {
  const [editingId, setEditingId] = useState(null);
  const [editPrice, setEditPrice] = useState('');
  const [recentChanges, setRecentChanges] = useState([]);
  const [isProcessing, setIsProcessing] = useState(null);
  const [showChangeLog, setShowChangeLog] = useState(false);
  const [showAgentStatus, setShowAgentStatus] = useState(true);
  const prevProductsRef = useRef(products);

  // React to real product data changes (from WebSocket / polling)
  useEffect(() => {
    const prev = prevProductsRef.current;
    if (isProcessing && prev && products) {
      const changed = products.some(p => {
        const old = prev.find(op => op.id === p.id);
        return old && old.our_price !== p.our_price;
      });
      if (changed) {
        setIsProcessing(null);
        setRecentChanges(cs =>
          cs.map((c, i) => (c.status === 'processing' ? { ...c, status: 'done' } : c))
        );
      }
    }
    prevProductsRef.current = products;
  }, [products, isProcessing]);

  const handleEditStart = (product) => {
    setEditingId(product.id);
    setEditPrice(product.competitor_price.toString());
  };

  const handleEditCancel = () => {
    setEditingId(null);
    setEditPrice('');
  };

  const handleEditSave = async (product) => {
    const newPrice = parseFloat(editPrice);
    if (isNaN(newPrice) || newPrice <= 0) return;

    setIsProcessing(product.id);
    try {
      const res = await fetch(`${API_BASE}/api/products/${product.id}/competitor-price`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ competitor_price: newPrice })
      });
      const data = await res.json();

      if (data.success) {
        setRecentChanges(prev => [{
          id: Date.now(),
          product_name: product.name,
          old_price: product.competitor_price,
          new_price: newPrice,
          our_old_price: product.our_price,
          timestamp: new Date().toISOString(),
          status: 'processing'
        }, ...prev].slice(0, 10));

        // Immediately refresh, then poll every 2s until the real update arrives
        onProductsRefresh();
        const poll = setInterval(() => onProductsRefresh(), 2000);
        // Safety fallback: stop polling after 20s if agent hasn't responded
        setTimeout(() => {
          clearInterval(poll);
          setIsProcessing(prev => {
            if (prev === product.id) {
              setRecentChanges(cs =>
                cs.map(c => (c.status === 'processing' ? { ...c, status: 'done' } : c))
              );
              return null;
            }
            return prev;
          });
        }, 20000);
      }
    } catch (e) {
      console.error('Failed to update competitor price:', e);
      setIsProcessing(null);
    }

    setEditingId(null);
    setEditPrice('');
  };

  const handleKeyDown = (e, product) => {
    if (e.key === 'Enter') handleEditSave(product);
    if (e.key === 'Escape') handleEditCancel();
  };

  const processingCount = recentChanges.filter(c => c.status === 'processing').length;

  return (
    <div className="space-y-6">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-600 via-violet-600 to-purple-700 p-8">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMSIgZmlsbD0icmdiYSgyNTUsMjU1LDI1NSwwLjA1KSIvPjwvc3ZnPg==')] opacity-50" />
        <div className="relative z-10">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-10 h-10 bg-white/20 backdrop-blur rounded-xl flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              <span className="text-green-200 text-xs font-medium uppercase tracking-wider">Agent Active</span>
            </div>
          </div>
          <h1 className="text-2xl font-bold text-white mb-1">Live Pricing Demo</h1>
          <p className="text-indigo-100 text-sm max-w-lg">
            Simulate competitor price changes and watch the AI agent instantly recalculate optimal pricing in real-time.
          </p>
        </div>
      </div>

      {/* How It Works - Horizontal Steps */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { step: '1', title: 'Pick a Product', desc: 'Choose any product card below', color: 'from-blue-500 to-blue-600' },
          { step: '2', title: 'Edit Price', desc: 'Change the competitor price', color: 'from-violet-500 to-violet-600' },
          { step: '3', title: 'Agent Detects', desc: 'AI instantly notices the change', color: 'from-amber-500 to-orange-500' },
          { step: '4', title: 'Auto Adjust', desc: 'Our price updates in real-time', color: 'from-emerald-500 to-green-600' },
        ].map(item => (
          <div key={item.step} className="bg-white rounded-xl border border-gray-100 p-4 flex items-start space-x-3">
            <div className={`w-8 h-8 bg-gradient-to-br ${item.color} rounded-lg flex items-center justify-center flex-shrink-0`}>
              <span className="text-white text-xs font-bold">{item.step}</span>
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-800">{item.title}</p>
              <p className="text-[11px] text-gray-400 mt-0.5">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Toolbar with Change Log Button */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <h2 className="text-lg font-bold text-gray-800">Products</h2>
          <span className="text-xs text-gray-400">{products.length} items &bull; Click competitor price to edit</span>
        </div>
        <button
          onClick={() => setShowChangeLog(!showChangeLog)}
          className={`relative flex items-center space-x-2 px-4 py-2 text-sm font-medium rounded-xl transition-all ${
            showChangeLog
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-200'
              : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 shadow-sm'
          }`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <span>Change Log</span>
          {recentChanges.length > 0 && (
            <span className={`absolute -top-1.5 -right-1.5 min-w-[20px] h-5 flex items-center justify-center text-[10px] font-bold rounded-full px-1.5 ${
              showChangeLog ? 'bg-white text-indigo-600' : 'bg-indigo-600 text-white'
            }`}>
              {recentChanges.length}
            </span>
          )}
        </button>
      </div>

      {/* Change Log Panel (togglable) */}
      {showChangeLog && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm animate-fade-in">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-gray-800">Recent Changes</h3>
              {processingCount > 0 && (
                <span className="flex items-center text-[10px] bg-amber-50 text-amber-600 px-2 py-0.5 rounded-full font-medium">
                  <svg className="w-3 h-3 mr-1 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  {processingCount} processing
                </span>
              )}
            </div>
            <button onClick={() => setShowChangeLog(false)} className="text-gray-400 hover:text-gray-600 transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="p-4">
            {recentChanges.length === 0 ? (
              <div className="text-center py-8">
                <div className="w-12 h-12 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-3">
                  <svg className="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-sm font-medium text-gray-400">No changes yet</p>
                <p className="text-xs text-gray-300 mt-1">Edit a competitor price to see the AI react</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {recentChanges.map(change => (
                  <div key={change.id} className={`rounded-xl p-3.5 border animate-fade-in ${
                    change.status === 'done'
                      ? 'bg-emerald-50/50 border-emerald-100'
                      : 'bg-amber-50/50 border-amber-100'
                  }`}>
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-xs font-semibold text-gray-800 truncate max-w-[180px]">{change.product_name}</span>
                      {change.status === 'done' ? (
                        <span className="flex items-center text-[10px] text-emerald-600 font-medium">
                          <svg className="w-3 h-3 mr-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                          </svg>
                          Done
                        </span>
                      ) : (
                        <span className="flex items-center text-[10px] text-amber-600 font-medium">
                          <svg className="w-3 h-3 mr-0.5 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                          Processing
                        </span>
                      )}
                    </div>
                    <div className="flex items-center text-xs text-gray-500 space-x-1.5">
                      <span className="font-medium">₹{change.old_price?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
                      <svg className="w-3 h-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                      <span className="font-bold text-violet-600">₹{change.new_price?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
                    </div>
                    <p className="text-[10px] text-gray-400 mt-1.5">
                      {new Date(change.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Product Cards - Full Width */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {products.map(product => {
          const diff = product.our_price - product.competitor_price;
          const diffPct = ((diff / product.competitor_price) * 100);
          const margin = product.profit_margin || ((product.our_price - product.cost_price) / product.our_price * 100);
          const isBeingProcessed = isProcessing === product.id;
          const isEditing = editingId === product.id;

          return (
            <div
              key={product.id}
              className={`bg-white rounded-2xl border shadow-sm transition-all duration-300 ${
                isBeingProcessed ? 'border-amber-300 ring-2 ring-amber-100 scale-[1.01]' : 'border-gray-100 hover:border-gray-200 hover:shadow-md'
              }`}
            >
              {/* Processing indicator */}
              {isBeingProcessed && (
                <div className="bg-gradient-to-r from-amber-50 to-orange-50 px-4 py-2 rounded-t-2xl border-b border-amber-100 flex items-center space-x-2">
                  <svg className="w-4 h-4 animate-spin text-amber-600" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <span className="text-xs font-medium text-amber-700">AI Agent is adjusting price...</span>
                </div>
              )}

              <div className="p-5">
                {/* Product Header */}
                <div className="flex items-start space-x-3 mb-4">
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="w-14 h-14 rounded-xl object-cover bg-gray-100 flex-shrink-0"
                    onError={(e) => { e.target.src = `https://via.placeholder.com/56/f3f4f6/6b7280?text=${product.category?.[0] || 'P'}`; }}
                  />
                  <div className="min-w-0 flex-1">
                    <h3 className="text-sm font-semibold text-gray-900 truncate">{product.name}</h3>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="text-[11px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{product.brand}</span>
                      <span className="text-[11px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{product.category}</span>
                    </div>
                  </div>
                </div>

                {/* Price Comparison */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  {/* Our Price */}
                  <div className="bg-emerald-50 rounded-xl p-3">
                    <p className="text-[10px] uppercase tracking-wider text-emerald-600 font-medium mb-1">Our Price</p>
                    <p className="text-lg font-bold text-emerald-700">
                      ₹{product.our_price?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                    </p>
                  </div>
                  {/* Competitor Price - Editable */}
                  <div
                    className={`rounded-xl p-3 cursor-pointer transition-all ${
                      isEditing ? 'bg-violet-100 ring-2 ring-violet-300' : 'bg-violet-50 hover:bg-violet-100'
                    }`}
                    onClick={() => !isEditing && handleEditStart(product)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-[10px] uppercase tracking-wider text-violet-600 font-medium">Competitor</p>
                      {!isEditing && (
                        <svg className="w-3 h-3 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                      )}
                    </div>
                    {isEditing ? (
                      <div className="flex items-center space-x-1">
                        <span className="text-violet-500 font-medium">₹</span>
                        <input
                          type="number"
                          value={editPrice}
                          onChange={(e) => setEditPrice(e.target.value)}
                          onKeyDown={(e) => handleKeyDown(e, product)}
                          autoFocus
                          className="w-full bg-white px-2 py-1 text-sm font-bold rounded-lg border border-violet-300 focus:outline-none focus:ring-2 focus:ring-violet-400 text-violet-700"
                        />
                      </div>
                    ) : (
                      <p className="text-lg font-bold text-violet-700">
                        ₹{product.competitor_price?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                      </p>
                    )}
                  </div>
                </div>

                {/* Edit Actions */}
                {isEditing && (
                  <div className="flex items-center space-x-2 mb-4">
                    <button
                      onClick={() => handleEditSave(product)}
                      className="flex-1 bg-violet-600 hover:bg-violet-700 text-white text-xs font-medium py-2 px-3 rounded-lg transition-colors flex items-center justify-center space-x-1"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>Apply Change</span>
                    </button>
                    <button
                      onClick={handleEditCancel}
                      className="bg-gray-100 hover:bg-gray-200 text-gray-600 text-xs font-medium py-2 px-3 rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                )}

                {/* Stats Row */}
                <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                  <div className="flex items-center space-x-3">
                    <div className="text-center">
                      <p className={`text-xs font-bold ${diff > 0 ? 'text-red-500' : 'text-emerald-500'}`}>
                        {diff > 0 ? '+' : ''}{diffPct.toFixed(1)}%
                      </p>
                      <p className="text-[9px] text-gray-400 uppercase">Gap</p>
                    </div>
                    <div className="w-px h-6 bg-gray-100" />
                    <div className="text-center">
                      <p className={`text-xs font-bold ${margin > 20 ? 'text-emerald-500' : margin > 10 ? 'text-amber-500' : 'text-red-500'}`}>
                        {margin?.toFixed(1)}%
                      </p>
                      <p className="text-[9px] text-gray-400 uppercase">Margin</p>
                    </div>
                    <div className="w-px h-6 bg-gray-100" />
                    <div className="text-center">
                      <p className="text-xs font-bold text-gray-700">{product.stock}</p>
                      <p className="text-[9px] text-gray-400 uppercase">Stock</p>
                    </div>
                  </div>
                  {!isBeingProcessed && (
                    <span className="inline-flex items-center text-[10px] bg-emerald-50 text-emerald-600 px-2 py-1 rounded-full font-medium">
                      <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full mr-1" />
                      Synced
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Floating Agent Status Card - Bottom Right */}
      {showAgentStatus && (
        <div className="fixed bottom-6 right-6 z-50 w-72 animate-fade-in">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl shadow-2xl shadow-slate-900/30 border border-slate-700/50 overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span className="text-xs font-semibold text-white">Agent Status</span>
              </div>
              <button
                onClick={() => setShowAgentStatus(false)}
                className="text-slate-500 hover:text-slate-300 transition-colors"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            {/* Body */}
            <div className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Response Time</span>
                <span className="text-xs font-bold text-white">~3s</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Mode</span>
                <span className="text-xs font-bold text-green-400">Real-time</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Pipeline</span>
                <span className="text-xs font-bold text-white">5 agents</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Changes</span>
                <span className="text-xs font-bold text-violet-400">{recentChanges.length}</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-1.5 mt-1">
                <div className={`h-1.5 rounded-full transition-all duration-1000 ${
                  isProcessing ? 'bg-gradient-to-r from-amber-400 to-orange-500 animate-pulse w-3/5' : 'bg-gradient-to-r from-violet-500 to-indigo-500 w-full'
                }`} />
              </div>
              <p className="text-[10px] text-slate-500">
                {isProcessing ? '⏳ Processing price adjustment...' : 'Market → Data → Pricing → Risk → Execute'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Floating button to reopen agent status if closed */}
      {!showAgentStatus && (
        <button
          onClick={() => setShowAgentStatus(true)}
          className="fixed bottom-6 right-6 z-50 w-12 h-12 bg-gradient-to-br from-slate-800 to-slate-900 rounded-full shadow-xl flex items-center justify-center text-white hover:scale-110 transition-transform border border-slate-700"
          title="Show Agent Status"
        >
          <span className="text-lg">🤖</span>
          <span className="absolute -top-0.5 -right-0.5 w-3 h-3 bg-green-400 rounded-full border-2 border-slate-900 animate-pulse" />
        </button>
      )}
    </div>
  );
}
