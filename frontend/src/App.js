import React, { useState, useEffect, useCallback, useRef } from 'react';
import Header from './components/Header';
import StatsBar from './components/StatsBar';
import ProductGrid from './components/ProductGrid';
import AgentActivityPanel from './components/AgentActivityPanel';
import DecisionLog from './components/DecisionLog';
import PriceCharts from './components/PriceCharts';
import NotificationPanel from './components/NotificationPanel';
import DemoPage from './components/DemoPage';
import AgentsUpdatePage from './components/AgentsUpdatePage';

const API_BASE = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws';

function App() {
  const [products, setProducts] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [activity, setActivity] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [stats, setStats] = useState({});
  const [agentStatus, setAgentStatus] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // WebSocket connection
  const connectWebSocket = useCallback(() => {
    try {
      const ws = new WebSocket(WS_URL);
      
      ws.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket connected');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      ws.onclose = () => {
        setIsConnected(false);
        // Reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.close();
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
    }
  }, []);

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'agent_status':
        setAgentStatus(prev => {
          const filtered = prev.filter(a => 
            !(a.agent === data.agent && a.product_id === data.product_id)
          );
          return [data, ...filtered].slice(0, 20);
        });
        break;
      case 'price_update':
        // Refresh products on price update
        fetchProducts();
        fetchDecisions();
        setNotifications(prev => [{
          id: Date.now(),
          title: `Price Updated: ${data.product_name}`,
          message: `₹${data.old_price?.toLocaleString()} → ₹${data.new_price?.toLocaleString()} (${data.change_percentage > 0 ? '+' : ''}${data.change_percentage?.toFixed(1)}%)`,
          type: data.decision_type === 'price_increase' ? 'success' : 'info',
          timestamp: new Date().toISOString()
        }, ...prev].slice(0, 30));
        break;
      case 'cycle_complete':
        fetchProducts();
        fetchStats();
        fetchActivity();
        break;
      case 'cycle_start':
        setAgentStatus(prev => [{
          agent: 'Orchestrator',
          status: 'running',
          step: `Starting cycle #${data.cycle_number}`,
          product_id: null
        }, ...prev].slice(0, 20));
        break;
      case 'competitor_update':
        fetchProducts();
        break;
      default:
        break;
    }
  };

  // API fetchers
  const fetchProducts = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/products`);
      const data = await res.json();
      if (data.success) setProducts(data.products);
    } catch (e) { console.error('Failed to fetch products:', e); }
  };

  const fetchDecisions = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/decisions`);
      const data = await res.json();
      if (data.success) setDecisions(data.decisions);
    } catch (e) { console.error('Failed to fetch decisions:', e); }
  };

  const fetchActivity = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/agent-activity`);
      const data = await res.json();
      if (data.success) setActivity(data.activity);
    } catch (e) { console.error('Failed to fetch activity:', e); }
  };

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/dashboard/stats`);
      const data = await res.json();
      if (data.success) setStats(data.stats);
    } catch (e) { console.error('Failed to fetch stats:', e); }
  };

  const fetchNotifications = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/notifications`);
      const data = await res.json();
      if (data.success) setNotifications(data.notifications);
    } catch (e) { console.error('Failed to fetch notifications:', e); }
  };

  // Initial data load
  useEffect(() => {
    fetchProducts();
    fetchDecisions();
    fetchActivity();
    fetchStats();
    fetchNotifications();
    connectWebSocket();

    // Polling fallback every 10s
    const interval = setInterval(() => {
      fetchProducts();
      fetchStats();
      fetchActivity();
      fetchDecisions();
    }, 10000);

    return () => {
      clearInterval(interval);
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, [connectWebSocket]);

  return (
    <div className="min-h-screen bg-[#f4f6f9]">
      <Header isConnected={isConnected} stats={stats} />
      
      {/* Navigation */}
      <div className="bg-white border-b sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center space-x-1 overflow-x-auto py-1">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>
              )},
              { id: 'demo', label: 'Live Demo', icon: (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
              )},
              { id: 'agents-update', label: 'Agent Updates', icon: (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
              )},
              { id: 'products', label: 'Products', icon: (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
              )},
              { id: 'analytics', label: 'Analytics', icon: (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
              )},
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-2.5 text-sm font-medium rounded-lg transition-all whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-gray-500 hover:text-gray-800 hover:bg-gray-50'
                }`}
              >
                <span className={activeTab === tab.id ? 'text-indigo-600' : 'text-gray-400'}>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <StatsBar stats={stats} />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <ProductGrid products={products} compact />
              </div>
              <div className="space-y-6">
                <AgentActivityPanel activity={agentStatus} liveActivity={activity} />
                <NotificationPanel notifications={notifications} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'demo' && (
          <DemoPage products={products} onProductsRefresh={fetchProducts} />
        )}

        {activeTab === 'products' && (
          <ProductGrid products={products} />
        )}

        {activeTab === 'agents-update' && (
          <AgentsUpdatePage onProductsRefresh={fetchProducts} />
        )}

        {activeTab === 'analytics' && (
          <PriceCharts products={products} fullView />
        )}
      </main>
    </div>
  );
}

export default App;
