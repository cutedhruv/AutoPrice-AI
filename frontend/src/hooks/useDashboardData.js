import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../services/api';

export function useDashboardData() {
  const [isLoading, setIsLoading] = useState(true);
  const [products, setProducts] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [updates, setUpdates] = useState([]);
  const [activity, setActivity] = useState([]);
  const [stats, setStats] = useState({});
  const [agentStatus, setAgentStatus] = useState([]);
  const [lastUpdatedAt, setLastUpdatedAt] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const fetchProducts = useCallback(async () => {
    try {
      const data = await api.getProducts();
      if (data.success) setProducts(data.products);
    } catch (e) {
      console.error('Failed to fetch products:', e);
    }
  }, []);

  const fetchDecisions = useCallback(async () => {
    try {
      const data = await api.getDecisions(30);
      if (data.success) setDecisions(data.decisions);
    } catch (e) {
      console.error('Failed to fetch decisions:', e);
    }
  }, []);

  const fetchUpdates = useCallback(async () => {
    try {
      const data = await api.getUpdates(40);
      if (data.success) setUpdates(data.updates);
    } catch (e) {
      console.error('Failed to fetch updates:', e);
    }
  }, []);

  const fetchActivity = useCallback(async () => {
    try {
      const data = await api.getActivity(50);
      if (data.success) setActivity(data.activity);
    } catch (e) {
      console.error('Failed to fetch activity:', e);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const data = await api.getStats();
      if (data.success) setStats(data.stats);
    } catch (e) {
      console.error('Failed to fetch stats:', e);
    }
  }, []);

  const refreshAll = useCallback(async () => {
    try {
      setIsLoading(true);
      await Promise.all([
        fetchProducts(),
        fetchDecisions(),
        fetchUpdates(),
        fetchActivity(),
        fetchStats(),
      ]);
      setLastUpdatedAt(new Date().toISOString());
    } finally {
      setIsLoading(false);
    }
  }, [fetchProducts, fetchDecisions, fetchUpdates, fetchActivity, fetchStats]);

  const handleWebSocketMessage = useCallback((data) => {
    setLastUpdatedAt(new Date().toISOString());
    switch (data.type) {
      case 'agent_status':
        setAgentStatus((prev) => {
          const filtered = prev.filter(
            (a) => !(a.agent === data.agent && a.product_id === data.product_id)
          );
          return [data, ...filtered].slice(0, 20);
        });
        break;
      case 'price_update':
        fetchProducts();
        fetchDecisions();
        fetchUpdates();
        break;
      case 'cycle_complete':
        fetchProducts();
        fetchStats();
        fetchActivity();
        break;
      case 'cycle_start':
        setAgentStatus((prev) => [
          {
            agent: 'Orchestrator',
            status: 'running',
            step: `Starting cycle #${data.cycle_number}`,
            product_id: null,
          },
          ...prev,
        ].slice(0, 20));
        break;
      case 'competitor_update':
        fetchProducts();
        break;
      default:
        break;
    }
  }, [fetchProducts, fetchDecisions, fetchUpdates, fetchStats, fetchActivity]);

  const connectWebSocket = useCallback(() => {
    try {
      const ws = new WebSocket(api.WS_URL);
      ws.onopen = () => setIsConnected(true);
      ws.onmessage = (event) => handleWebSocketMessage(JSON.parse(event.data));
      ws.onclose = () => {
        setIsConnected(false);
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
      };
      ws.onerror = () => ws.close();
      wsRef.current = ws;
    } catch {
      reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
    }
  }, [handleWebSocketMessage]);

  useEffect(() => {
    refreshAll();
    connectWebSocket();
    const interval = setInterval(() => refreshAll(), 10000);
    return () => {
      clearInterval(interval);
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, [refreshAll, connectWebSocket]);

  return {
    products,
    decisions,
    updates,
    activity,
    stats,
    agentStatus,
    isConnected,
    isLoading,
    lastUpdatedAt,
    fetchProducts,
    fetchDecisions,
    fetchUpdates,
  };
}

