import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, AreaChart, Area, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  PieChart, Pie, Cell, ComposedChart, Scatter
} from 'recharts';

const API_BASE = 'http://localhost:8000';
const COLORS = ['#6366f1', '#2874f0', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#06b6d4'];

function KpiMini({ label, value, sub, color }) {
  return (
    <div className="bg-gray-50 rounded-xl p-4 text-center">
      <p className="text-[9px] text-gray-400 uppercase tracking-wider font-semibold">{label}</p>
      <p className={`text-xl font-extrabold ${color || 'text-gray-800'} mt-1`}>{value}</p>
      {sub && <p className="text-[10px] text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
}

export default function PriceCharts({ products, fullView }) {
  const [trends, setTrends] = useState({});
  const [decisions, setDecisions] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);

  const fetchTrends = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/analytics/price-trends`);
      const data = await res.json();
      if (data.success) {
        setTrends(data.trends);
        const firstKey = Object.keys(data.trends)[0];
        if (firstKey && !selectedProduct) setSelectedProduct(firstKey);
      }
    } catch (e) { console.error('Failed to fetch trends:', e); }
  }, [selectedProduct]);

  const fetchDecisions = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/decisions?limit=100`);
      const data = await res.json();
      if (data.success) setDecisions(data.decisions || []);
    } catch (e) { console.error('Failed to fetch decisions:', e); }
  }, []);

  useEffect(() => {
    fetchTrends();
    fetchDecisions();
    const interval = setInterval(() => { fetchTrends(); fetchDecisions(); }, 15000);
    return () => clearInterval(interval);
  }, [fetchTrends, fetchDecisions]);

  // === Derived data ===

  // Price comparison (Our vs Competitor)
  const comparisonData = products.map(p => ({
    name: p.name?.length > 18 ? p.name.substring(0, 18) + '…' : p.name,
    fullName: p.name,
    ourPrice: p.our_price,
    competitorPrice: p.competitor_price,
    gap: Math.round(p.our_price - p.competitor_price),
    gapPct: ((p.our_price - p.competitor_price) / p.competitor_price * 100).toFixed(1),
    margin: p.profit_margin,
  }));

  // Margin vs Demand scatter
  const marginDemandData = products.map(p => ({
    name: p.name?.substring(0, 15),
    margin: p.profit_margin,
    demand: Math.round(p.demand_score * 100),
    stock: p.stock,
    price: p.our_price,
  }));

  // Competitive position radar
  const radarData = products.map(p => ({
    product: p.name?.substring(0, 12),
    margin: Math.min(p.profit_margin, 30),
    demand: p.demand_score * 100,
    competitiveness: Math.max(0, 100 - Math.abs((p.our_price - p.competitor_price) / p.competitor_price * 100) * 10),
    stock: Math.min(p.stock, 100),
  }));

  // Decision type pie
  const decisionCounts = decisions.reduce((acc, d) => {
    acc[d.decision_type] = (acc[d.decision_type] || 0) + 1;
    return acc;
  }, {});
  const pieData = [
    { name: 'Increases', value: decisionCounts['price_increase'] || 0, color: '#10b981' },
    { name: 'Decreases', value: decisionCounts['price_decrease'] || 0, color: '#3b82f6' },
    { name: 'No Change', value: decisionCounts['no_change'] || 0, color: '#94a3b8' },
  ];

  // Price gap chart (how far below/above competitor)
  const gapData = products.map(p => {
    const gap = ((p.our_price - p.competitor_price) / p.competitor_price * 100);
    return {
      name: p.name?.substring(0, 14),
      gap: Math.round(gap * 10) / 10,
      fill: gap <= 0 ? '#10b981' : '#ef4444',
    };
  });

  // Selected product trend
  const selectedTrend = (selectedProduct && trends[selectedProduct]?.data) || [];

  // KPIs
  const avgMargin = products.length ? (products.reduce((s, p) => s + p.profit_margin, 0) / products.length).toFixed(1) : 0;
  const belowCompetitor = products.filter(p => p.our_price < p.competitor_price).length;
  const avgGap = products.length ? (products.reduce((s, p) => s + ((p.our_price - p.competitor_price) / p.competitor_price * 100), 0) / products.length).toFixed(1) : 0;
  const totalRevenue = products.reduce((s, p) => s + p.our_price * Math.max(1, Math.floor(p.stock / 10)), 0);

  const ChartTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white/95 backdrop-blur p-3 border border-gray-200 rounded-xl shadow-lg max-w-[220px]">
          <p className="text-[11px] font-bold text-gray-700 mb-1">{label || payload[0]?.payload?.fullName || ''}</p>
          {payload.map((entry, idx) => (
            <p key={idx} className="text-[11px]" style={{ color: entry.color }}>
              {entry.name}: {typeof entry.value === 'number' && entry.value > 1000 ? `₹${entry.value.toLocaleString('en-IN')}` : entry.value}{entry.unit || ''}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-600 via-violet-600 to-purple-700 p-6">
        <div className="relative z-10">
          <h1 className="text-xl font-bold text-white mb-1">Analytics & Price Intelligence</h1>
          <p className="text-indigo-100 text-sm">Real-time competitive insights, margin analysis, and pricing performance.</p>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        <KpiMini label="Products" value={products.length} color="text-indigo-700" />
        <KpiMini label="Avg Margin" value={`${avgMargin}%`} color={parseFloat(avgMargin) > 15 ? 'text-emerald-600' : 'text-amber-600'} />
        <KpiMini label="Below Competitor" value={`${belowCompetitor}/${products.length}`} color="text-emerald-600" sub="competitive" />
        <KpiMini label="Avg Gap" value={`${avgGap}%`} color={parseFloat(avgGap) <= 0 ? 'text-emerald-600' : 'text-red-500'} sub="vs competitor" />
        <KpiMini label="Total Decisions" value={decisions.length} color="text-violet-700" />
        <KpiMini label="Est. Revenue" value={`₹${(totalRevenue / 100000).toFixed(1)}L`} color="text-blue-700" sub="projected" />
      </div>

      {/* Row 1: Price Comparison + Competitive Gap */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <h3 className="text-sm font-bold text-gray-700 mb-4">Our Price vs Competitor</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={comparisonData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `₹${(v / 1000).toFixed(0)}k`} />
              <Tooltip content={<ChartTooltip />} />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Bar dataKey="ourPrice" name="Our Price" fill="#6366f1" radius={[4, 4, 0, 0]} />
              <Bar dataKey="competitorPrice" name="Competitor" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <h3 className="text-sm font-bold text-gray-700 mb-4">Decision Breakdown</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                {pieData.map((entry, idx) => (
                  <Cell key={idx} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-2">
            {pieData.map((d, i) => (
              <div key={i} className="flex items-center space-x-1">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                <span className="text-[10px] text-gray-500">{d.name}: {d.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Row 2: Competitive Gap + Margin/Demand */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <h3 className="text-sm font-bold text-gray-700 mb-1">Competitive Gap</h3>
          <p className="text-[10px] text-gray-400 mb-4">Green = below competitor (winning), Red = above competitor</p>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={gapData} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={v => `${v}%`} domain={['auto', 'auto']} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={100} />
              <Tooltip formatter={(v) => `${v}%`} />
              <Bar dataKey="gap" name="Gap %" radius={[0, 4, 4, 0]}>
                {gapData.map((entry, idx) => (
                  <Cell key={idx} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <h3 className="text-sm font-bold text-gray-700 mb-4">Margin vs Demand vs Stock</h3>
          <ResponsiveContainer width="100%" height={250}>
            <ComposedChart data={marginDemandData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis yAxisId="left" tick={{ fontSize: 10 }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Bar yAxisId="left" dataKey="margin" name="Margin %" fill="#10b981" radius={[3, 3, 0, 0]} />
              <Bar yAxisId="left" dataKey="demand" name="Demand %" fill="#8b5cf6" radius={[3, 3, 0, 0]} />
              <Line yAxisId="right" type="monotone" dataKey="stock" name="Stock" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row 3: Price Trend + Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-gray-700">Price History Trend</h3>
            <select
              value={selectedProduct || ''}
              onChange={(e) => setSelectedProduct(e.target.value)}
              className="text-xs border border-gray-200 rounded-lg px-3 py-1.5 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-200"
            >
              {Object.entries(trends).map(([id, data]) => (
                <option key={id} value={id}>{data.name?.substring(0, 30)}</option>
              ))}
            </select>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={selectedTrend}>
              <defs>
                <linearGradient id="ourGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="compGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} tickFormatter={t => new Date(t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} />
              <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `₹${(v / 1000).toFixed(0)}k`} />
              <Tooltip content={<ChartTooltip />} />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Area type="monotone" dataKey="our_price" name="Our Price" stroke="#6366f1" strokeWidth={2} fill="url(#ourGrad)" />
              <Area type="monotone" dataKey="competitor_price" name="Competitor" stroke="#f59e0b" strokeWidth={2} fill="url(#compGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <h3 className="text-sm font-bold text-gray-700 mb-4">Competitiveness Radar</h3>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="product" tick={{ fontSize: 9 }} />
              <PolarRadiusAxis tick={{ fontSize: 9 }} />
              <Radar name="Margin" dataKey="margin" stroke="#10b981" fill="#10b981" fillOpacity={0.15} />
              <Radar name="Demand" dataKey="demand" stroke="#6366f1" fill="#6366f1" fillOpacity={0.15} />
              <Radar name="Competitiveness" dataKey="competitiveness" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.15} />
              <Legend wrapperStyle={{ fontSize: '10px' }} />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row 4: Product Performance Table */}
      {fullView && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-gray-100">
            <h3 className="text-sm font-bold text-gray-700">Product Performance Summary</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-gray-50 text-left">
                  <th className="px-4 py-2.5 font-semibold text-gray-500">Product</th>
                  <th className="px-4 py-2.5 font-semibold text-gray-500 text-right">Our Price</th>
                  <th className="px-4 py-2.5 font-semibold text-gray-500 text-right">Competitor</th>
                  <th className="px-4 py-2.5 font-semibold text-gray-500 text-right">Gap</th>
                  <th className="px-4 py-2.5 font-semibold text-gray-500 text-right">Margin</th>
                  <th className="px-4 py-2.5 font-semibold text-gray-500 text-right">Demand</th>
                  <th className="px-4 py-2.5 font-semibold text-gray-500 text-right">Stock</th>
                  <th className="px-4 py-2.5 font-semibold text-gray-500 text-center">Status</th>
                </tr>
              </thead>
              <tbody>
                {products.map((p, i) => {
                  const gap = ((p.our_price - p.competitor_price) / p.competitor_price * 100);
                  return (
                    <tr key={p.id} className={`border-t border-gray-50 ${i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'} hover:bg-indigo-50/30`}>
                      <td className="px-4 py-2.5 font-medium text-gray-800">{p.name}</td>
                      <td className="px-4 py-2.5 text-right font-bold text-gray-700">₹{p.our_price?.toLocaleString('en-IN')}</td>
                      <td className="px-4 py-2.5 text-right text-gray-500">₹{p.competitor_price?.toLocaleString('en-IN')}</td>
                      <td className={`px-4 py-2.5 text-right font-bold ${gap <= 0 ? 'text-emerald-600' : 'text-red-500'}`}>{gap.toFixed(1)}%</td>
                      <td className={`px-4 py-2.5 text-right font-bold ${p.profit_margin > 15 ? 'text-emerald-600' : p.profit_margin > 8 ? 'text-amber-600' : 'text-red-500'}`}>{p.profit_margin?.toFixed(1)}%</td>
                      <td className="px-4 py-2.5 text-right">
                        <div className="inline-flex items-center space-x-1">
                          <div className="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${p.demand_score * 100}%` }} />
                          </div>
                          <span className="text-gray-500">{(p.demand_score * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-2.5 text-right text-gray-600">{p.stock}</td>
                      <td className="px-4 py-2.5 text-center">
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${gap <= 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
                          {gap <= 0 ? 'Winning' : 'Losing'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
