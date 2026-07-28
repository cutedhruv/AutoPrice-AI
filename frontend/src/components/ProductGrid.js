import React from 'react';

function ProductCard({ product }) {
  const priceChange = product.our_price - product.competitor_price;
  const isAboveCompetitor = priceChange > 0;
  const marginColor = product.profit_margin > 20 ? 'text-emerald-600' : 
                      product.profit_margin > 10 ? 'text-amber-600' : 'text-red-500';

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden group">
      {/* Image */}
      <div className="relative h-44 bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center overflow-hidden">
        <img
          src={product.image_url}
          alt={product.name}
          className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-500"
          onError={(e) => {
            e.target.src = `https://via.placeholder.com/400x300/f8f9fa/6c757d?text=${encodeURIComponent(product.category)}`;
          }}
        />
        <span className="absolute top-3 left-3 bg-slate-900/80 backdrop-blur-sm text-white text-[10px] px-2.5 py-1 rounded-full font-medium">
          {product.category}
        </span>
        <div className="absolute bottom-0 inset-x-0 h-12 bg-gradient-to-t from-black/20 to-transparent" />
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="flex items-start justify-between mb-1">
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-gray-900 truncate">{product.name}</h3>
            <p className="text-[11px] text-gray-400 mt-0.5">{product.brand}</p>
          </div>
          <div className="flex items-center bg-amber-50 px-1.5 py-0.5 rounded-md ml-2">
            <span className="text-[11px] text-amber-600 font-medium">★ {product.rating}</span>
          </div>
        </div>

        {/* Price */}
        <div className="mt-3">
          <div className="flex items-baseline justify-between">
            <span className="text-lg font-bold text-gray-900">
              ₹{product.our_price?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </span>
            <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
              isAboveCompetitor 
                ? 'bg-red-50 text-red-600' 
                : 'bg-emerald-50 text-emerald-600'
            }`}>
              {isAboveCompetitor ? '▲' : '▼'} {Math.abs((priceChange / product.competitor_price) * 100).toFixed(1)}%
            </span>
          </div>
          <p className="text-[11px] text-gray-400 mt-1">
            vs ₹{product.competitor_price?.toLocaleString('en-IN', { maximumFractionDigits: 0 })} competitor
          </p>
        </div>

        {/* Metrics */}
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-50">
          <div className="text-center">
            <p className={`text-xs font-bold ${marginColor}`}>{product.profit_margin?.toFixed(0)}%</p>
            <p className="text-[10px] text-gray-400">Margin</p>
          </div>
          <div className="text-center">
            <p className="text-xs font-bold text-gray-700">{product.stock}</p>
            <p className="text-[10px] text-gray-400">Stock</p>
          </div>
          <div className="text-center">
            <div className="w-10 h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-400 to-violet-500 rounded-full"
                style={{ width: `${product.demand_score * 100}%` }}
              />
            </div>
            <p className="text-[10px] text-gray-400 mt-0.5">Demand</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ProductGrid({ products, compact }) {
  const displayProducts = compact ? products.slice(0, 6) : products;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-bold text-gray-800">
          {compact ? 'Product Overview' : 'All Products'}
        </h2>
        <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded-full">{products.length} items</span>
      </div>
      <div className={`grid gap-4 ${
        compact 
          ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' 
          : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
      }`}>
        {displayProducts.map(product => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </div>
  );
}
