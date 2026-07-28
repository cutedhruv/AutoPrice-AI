import React, { useEffect, useMemo, useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar,
} from 'recharts';

const API_BASE = 'http://localhost:8000';

const badgeClass = {
  Competitive: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  Undervalued: 'bg-blue-100 text-blue-700 border-blue-200',
  Overpriced: 'bg-rose-100 text-rose-700 border-rose-200',
};

function formatMoney(v) {
  if (v === undefined || v === null) return '--';
  return `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

function shortTime(ts) {
  if (!ts) return '--';
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function getBadge(product) {
  const gapPct = ((product.our_price - product.competitor_price) / product.competitor_price) * 100;
  if (gapPct > 2.5) return 'Overpriced';
  if (gapPct < -2.5) return 'Undervalued';
  return 'Competitive';
}

function trendArrow(value) {
  if (value > 0) return { icon: '▲', cls: 'text-emerald-600' };
  if (value < 0) return { icon: '▼', cls: 'text-rose-600' };
  return { icon: '•', cls: 'text-slate-400' };
}

export default function DashboardPage({ products, decisions, agentStatus, activity, stats, isLoading, isDark }) {
  const [selectedId, setSelectedId] = useState(null);
  const [trends, setTrends] = useState({});
  const [loadingTrends, setLoadingTrends] = useState(false);

  useEffect(() => {
    if (!products?.length) return;
    if (!selectedId || !products.find((p) => p.id === selectedId)) {
      setSelectedId(products[0].id);
    }
  }, [products, selectedId]);

  useEffect(() => {
    const load = async () => {
      try {
        setLoadingTrends(true);
        const res = await fetch(`${API_BASE}/api/analytics/price-trends`);
        const data = await res.json();
        if (data.success) setTrends(data.trends || {});
      } catch (e) {
        console.error('Failed to load trend data:', e);
      } finally {
        setLoadingTrends(false);
      }
    };
    load();
  }, []);

  const selectedProduct = useMemo(
    () => products.find((p) => p.id === selectedId) || products[0],
    [products, selectedId]
  );

  const selectedTrend = useMemo(() => {
    if (!selectedProduct) return [];
    return trends[String(selectedProduct.id)]?.data || [];
  }, [selectedProduct, trends]);

  const comparisonData = useMemo(
    () =>
      products.slice(0, 8).map((p) => ({
        name: p.name.length > 14 ? `${p.name.slice(0, 14)}...` : p.name,
        ours: p.our_price,
        competitor: p.competitor_price,
      })),
    [products]
  );

  const latestDecision = decisions?.[0];
  const recentActivity = agentStatus?.slice(0, 8) || [];
  const timeline = activity?.slice(0, 10) || [];
  const groupedTimeline = useMemo(() => {
    const grouped = {};
    timeline.forEach((item) => {
      const key = item.agent_name || 'Unknown Agent';
      if (!grouped[key]) grouped[key] = [];
      grouped[key].push(item);
    });
    return Object.entries(grouped);
  }, [timeline]);

  const kpis = [
    {
      title: 'Current Price',
      value: formatMoney(selectedProduct?.our_price),
      trend: selectedProduct ? selectedProduct.our_price - selectedProduct.competitor_price : 0,
      tooltip: 'Current selling price of selected product.',
    },
    {
      title: 'Competitor Price',
      value: formatMoney(selectedProduct?.competitor_price),
      trend: selectedProduct ? selectedProduct.competitor_price - selectedProduct.our_price : 0,
      tooltip: 'Primary competitor anchor currently used by market agent.',
    },
    {
      title: 'Profit Margin',
      value: `${(selectedProduct?.profit_margin || 0).toFixed(2)}%`,
      trend: (selectedProduct?.profit_margin || 0) - 12,
      tooltip: 'Current estimated product margin percentage.',
    },
    {
      title: 'Demand Level',
      value: `${Math.round((selectedProduct?.demand_score || 0) * 100)}%`,
      trend: (selectedProduct?.demand_score || 0) - 0.5,
      tooltip: 'Demand signal score from market + data analysis.',
    },
  ];

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
      {/* Left panel */}
      <aside className="xl:col-span-3 space-y-4">
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-900">Products & Market</h3>
          <p className="text-xs text-slate-500 mt-1">Live product positioning vs competitor anchor.</p>
        </div>

        <div className="space-y-3 max-h-[74vh] overflow-y-auto pr-1">
          {products.map((product) => {
            const badge = getBadge(product);
            const delta = product.our_price - product.competitor_price;
            const deltaPct = (delta / product.competitor_price) * 100;
            const selected = selectedId === product.id;
            return (
              <button
                key={product.id}
                onClick={() => setSelectedId(product.id)}
                className={`w-full text-left border rounded-2xl p-4 shadow-sm transition-all ${
                  isDark ? 'bg-slate-900 border-slate-700 hover:border-slate-600' : 'bg-white'
                } ${
                  selected
                    ? 'border-indigo-300 ring-2 ring-indigo-100'
                    : 'border-slate-200 hover:border-slate-300 hover:shadow-md'
                }`}
              >
                <div className="flex items-start gap-3">
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="w-12 h-12 rounded-xl object-cover bg-slate-100"
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-slate-900 truncate">{product.name}</p>
                    <span
                      className={`inline-flex mt-1 px-2 py-0.5 text-[10px] rounded-md border font-semibold ${badgeClass[badge]}`}
                    >
                      {badge}
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 mt-3">
                  <div className="bg-slate-50 rounded-lg p-2">
                    <p className="text-[10px] uppercase text-slate-500">Our price</p>
                    <p className="text-sm font-semibold text-slate-800">{formatMoney(product.our_price)}</p>
                  </div>
                  <div className="bg-slate-50 rounded-lg p-2">
                    <p className="text-[10px] uppercase text-slate-500">Competitor</p>
                    <p className="text-sm font-semibold text-slate-800">{formatMoney(product.competitor_price)}</p>
                  </div>
                </div>
                <div className="h-10 mt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={(trends[String(product.id)]?.data || []).slice(-12)}>
                      <Line type="monotone" dataKey="our_price" stroke="#4f46e5" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <p className={`mt-2 text-xs font-medium ${delta > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                  {delta > 0 ? '+' : ''}{formatMoney(delta)} ({deltaPct > 0 ? '+' : ''}{deltaPct.toFixed(2)}%)
                </p>
              </button>
            );
          })}
        </div>
      </aside>

      {/* Center panel */}
      <section className="xl:col-span-6 space-y-4">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {isLoading
            ? Array.from({ length: 4 }).map((_, idx) => (
              <div key={`kpi-skeleton-${idx}`} className={`border rounded-2xl p-4 shadow-sm animate-pulse ${
                isDark ? 'bg-slate-900 border-slate-700' : 'bg-white border-slate-200'
              }`}>
                <div className="h-3 bg-slate-200 rounded w-1/2 mb-3" />
                <div className="h-6 bg-slate-200 rounded w-2/3 mb-2" />
                <div className="h-3 bg-slate-200 rounded w-1/3" />
              </div>
            ))
            : kpis.map((kpi) => {
            const t = trendArrow(kpi.trend);
            return (
              <div key={kpi.title} className={`border rounded-2xl p-4 shadow-sm ${
                isDark ? 'bg-slate-900 border-slate-700' : 'bg-white border-slate-200'
              }`} title={kpi.tooltip}>
                <p className="text-xs text-slate-500">{kpi.title}</p>
                <p className="text-lg font-semibold text-slate-900 mt-1">{kpi.value}</p>
                <p className={`text-xs font-semibold mt-1 ${t.cls}`}>{t.icon} trend</p>
              </div>
            );
          })}
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-900">Price Comparison Chart</h3>
            <span className="text-xs text-slate-500">Our vs competitor over time</span>
          </div>
          <div className="h-72">
            {loadingTrends ? (
              <div className="h-full rounded-xl bg-slate-100 animate-pulse" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={selectedTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="timestamp"
                    tick={{ fontSize: 10 }}
                    tickFormatter={(v) => new Date(v).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="our_price" stroke="#4f46e5" strokeWidth={2.2} dot={false} />
                  <Line type="monotone" dataKey="competitor_price" stroke="#06b6d4" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-900">Profit Trend Graph</h3>
              <span className="text-xs text-slate-500">Margin and spread view</span>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={selectedTrend.map((row) => ({
                    ...row,
                    margin_proxy: row.our_price && selectedProduct?.cost_price
                      ? ((row.our_price - selectedProduct.cost_price) / row.our_price) * 100
                      : 0,
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="timestamp" hide />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="margin_proxy" stroke="#16a34a" strokeWidth={2.2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-900">Portfolio Price Spread</h3>
              <span className="text-xs text-slate-500">Cross-product view</span>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={comparisonData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="ours" fill="#4f46e5" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="competitor" fill="#0ea5e9" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </section>

      {/* Right panel */}
      <aside className="xl:col-span-3 space-y-4">
        <div className={`border rounded-2xl p-4 shadow-sm ${isDark ? 'bg-slate-900 border-slate-700' : 'bg-white border-slate-200'}`}>
          <h3 className="text-sm font-semibold text-slate-900">Agent Intelligence</h3>
          <p className="text-xs text-slate-500 mt-1">Live orchestration + explainability stream.</p>
        </div>

        <div className={`border rounded-2xl p-4 shadow-sm ${isDark ? 'bg-slate-900 border-slate-700' : 'bg-white border-slate-200'}`}>
          <p className="text-xs text-slate-500 mb-3">Current Agent Status</p>
          <div className="space-y-2 max-h-56 overflow-y-auto">
            {recentActivity.length === 0 ? (
              <p className="text-xs text-slate-400">Waiting for activity...</p>
            ) : (
              recentActivity.map((item, idx) => (
                <div key={`${item.agent}-${idx}`} className={`border rounded-xl p-3 transition-colors ${
                  isDark ? 'border-slate-700 hover:bg-slate-800' : 'border-slate-100 hover:bg-slate-50'
                }`}>
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs font-semibold text-slate-800">{item.agent}</p>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      item.status === 'running'
                        ? 'bg-amber-100 text-amber-700'
                        : item.status === 'error'
                          ? 'bg-rose-100 text-rose-700'
                          : 'bg-emerald-100 text-emerald-700'
                    }`}>
                      {item.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 mt-1">{item.step}</p>
                </div>
              ))
            )}
          </div>
        </div>

        <div className={`border rounded-2xl p-4 shadow-sm ${isDark ? 'bg-slate-900 border-slate-700' : 'bg-white border-slate-200'}`}>
          <p className="text-xs text-slate-500 mb-2">Decision Explanation</p>
          {!latestDecision ? (
            <p className="text-xs text-slate-400">No decisions yet.</p>
          ) : (
            <div className="space-y-2">
              <p className="text-sm font-semibold text-slate-900">{latestDecision.product_name}</p>
              <p className="text-xs text-slate-600">
                {formatMoney(latestDecision.old_price)} → {formatMoney(latestDecision.new_price)}
              </p>
              <p className="text-xs text-slate-600 leading-relaxed">{latestDecision.reason}</p>
              <div className="grid grid-cols-3 gap-2 pt-1">
                <div className="bg-slate-50 rounded-lg p-2">
                  <p className="text-[10px] text-slate-500">Competitor</p>
                  <p className="text-xs font-semibold text-slate-800">{formatMoney(latestDecision.competitor_price)}</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-2">
                  <p className="text-[10px] text-slate-500">Demand</p>
                  <p className="text-xs font-semibold text-slate-800">{Math.round((selectedProduct?.demand_score || 0) * 100)}%</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-2">
                  <p className="text-[10px] text-slate-500">Stock</p>
                  <p className="text-xs font-semibold text-slate-800">{selectedProduct?.stock ?? '--'}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className={`border rounded-2xl p-4 shadow-sm ${isDark ? 'bg-slate-900 border-slate-700' : 'bg-white border-slate-200'}`}>
          <p className="text-xs text-slate-500 mb-3">Timeline (Last 10 actions)</p>
          <div className="space-y-3 max-h-72 overflow-y-auto">
            {groupedTimeline.length === 0 ? (
              <p className="text-xs text-slate-400">No timeline entries yet.</p>
            ) : (
              groupedTimeline.map(([agent, entries]) => (
                <div key={agent} className="border border-slate-100 rounded-xl p-2.5">
                  <p className="text-xs font-semibold text-slate-700 mb-1">
                    {agent} <span className="text-slate-400">({entries.length} actions)</span>
                  </p>
                  <div className="space-y-1">
                    {entries.slice(0, 4).map((item, idx) => (
                      <div key={`${item.id || idx}`} className="flex gap-2">
                        <div className="w-1.5 h-1.5 mt-1.5 rounded-full bg-indigo-500" />
                        <div className="min-w-0">
                          <p className="text-[11px] font-medium text-slate-800 truncate">{item.action}</p>
                          <p className="text-[10px] text-slate-500 truncate">{item.details}</p>
                          <p className="text-[10px] text-slate-400">{shortTime(item.timestamp)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-2xl p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-indigo-100">System Metrics</p>
          <div className="grid grid-cols-2 gap-3 mt-3 text-xs">
            <div>
              <p className="text-indigo-100">Cycles</p>
              <p className="text-lg font-semibold">{stats?.total_cycles ?? 0}</p>
            </div>
            <div>
              <p className="text-indigo-100">Updates</p>
              <p className="text-lg font-semibold">{stats?.total_updates ?? 0}</p>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}
