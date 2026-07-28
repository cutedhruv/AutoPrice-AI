import React from 'react';

export default function StatsBar({ stats }) {
  const statCards = [
    {
      label: 'Products',
      value: stats?.total_products || 0,
      icon: '📦',
      gradient: 'from-blue-500/10 to-blue-600/5',
      border: 'border-blue-100',
      textColor: 'text-blue-700'
    },
    {
      label: 'Price Updates',
      value: stats?.total_updates || 0,
      icon: '⚡',
      gradient: 'from-emerald-500/10 to-emerald-600/5',
      border: 'border-emerald-100',
      textColor: 'text-emerald-700'
    },
    {
      label: 'Avg Margin',
      value: `${stats?.avg_margin || 0}%`,
      icon: '📈',
      gradient: 'from-violet-500/10 to-violet-600/5',
      border: 'border-violet-100',
      textColor: 'text-violet-700'
    },
    {
      label: 'Competitive',
      value: stats?.products_below_competitor || 0,
      icon: '🏆',
      gradient: 'from-amber-500/10 to-amber-600/5',
      border: 'border-amber-100',
      textColor: 'text-amber-700'
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {statCards.map((stat, idx) => (
        <div
          key={idx}
          className={`bg-gradient-to-br ${stat.gradient} border ${stat.border} rounded-2xl p-4 transition-all hover:shadow-md`}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xl">{stat.icon}</span>
            <span className="text-[10px] uppercase tracking-wider text-gray-400 font-medium">{stat.label}</span>
          </div>
          <p className={`text-2xl font-bold ${stat.textColor}`}>{stat.value}</p>
        </div>
      ))}
    </div>
  );
}
