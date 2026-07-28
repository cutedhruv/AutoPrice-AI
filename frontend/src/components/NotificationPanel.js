import React from 'react';

export default function NotificationPanel({ notifications }) {
  const typeIcons = {
    success: '✅',
    info: 'ℹ️',
    warning: '⚠️',
    error: '❌'
  };

  const typeColors = {
    success: 'border-l-green-400',
    info: 'border-l-blue-400',
    warning: 'border-l-yellow-400',
    error: 'border-l-red-400'
  };

  const timeAgo = (timestamp) => {
    const diff = Date.now() - new Date(timestamp).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'now';
    if (mins < 60) return `${mins}m`;
    const hrs = Math.floor(mins / 60);
    return `${hrs}h`;
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-gray-800">Notifications</h3>
          <span className="bg-violet-100 text-violet-600 text-[10px] font-bold px-2 py-0.5 rounded-full">
            {notifications.length}
          </span>
        </div>
      </div>
      <div className="p-3 space-y-2 max-h-64 overflow-y-auto">
        {notifications.length === 0 ? (
          <p className="text-xs text-gray-400 text-center py-4">No notifications yet</p>
        ) : (
          notifications.slice(0, 8).map((notif, idx) => (
            <div
              key={notif.id || idx}
              className={`border-l-4 ${typeColors[notif.type] || 'border-l-gray-300'} bg-gray-50 p-3 rounded-r-lg animate-fade-in`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-2">
                  <span className="text-sm">{typeIcons[notif.type] || '📌'}</span>
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-gray-800 truncate">{notif.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{notif.message}</p>
                  </div>
                </div>
                <span className="text-xs text-gray-400 whitespace-nowrap ml-2">
                  {timeAgo(notif.timestamp)}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
