import React from 'react';
import { Plus, MessageSquare, Trash2, Database, Wifi, WifiOff } from 'lucide-react';
import { clearMemoryCache } from '../api';

const Sidebar = ({ 
  sessions, 
  activeSessionId, 
  onSelectSession, 
  onNewChat, 
  onDeleteSession, 
  backendOnline 
}) => {

  const handleClearCache = async () => {
    if (window.confirm("Are you sure you want to clear all weather cache memory? This will wipe the SQLite weather cache and ChromaDB vectors.")) {
      try {
        const res = await clearMemoryCache();
        if (res.success) {
          alert("All weather memories cleared successfully.");
        }
      } catch (err) {
        console.error("Failed to clear weather memory:", err);
        alert("Error clearing weather memory.");
      }
    }
  };

  return (
    <aside className="w-64 bg-zinc-950 border-r border-zinc-900 flex flex-col h-full z-20 flex-shrink-0">
      
      {/* Brand Header */}
      <div className="h-16 flex items-center gap-2.5 px-6 border-b border-zinc-900">
        <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-900/30">
          <Database className="w-4 h-4 text-white animate-pulse" />
        </div>
        <div className="flex flex-col">
          <span className="font-bold text-zinc-100 tracking-tight text-sm">AURA WEATHER</span>
          <span className="text-[9px] text-indigo-400 font-semibold tracking-wider uppercase">AI Agent with Memory</span>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-4 border-b border-zinc-900/60">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 hover:text-indigo-300 text-zinc-200 text-sm font-semibold transition-all duration-150 shadow-sm"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1.5 scrollbar-thin">
        <span className="text-[10px] font-bold text-zinc-600 px-3 uppercase tracking-wider block mb-2">
          Previous Chats
        </span>
        
        {sessions.length === 0 ? (
          <div className="text-xs text-zinc-500 text-center py-8 font-medium italic">
            No chats started yet
          </div>
        ) : (
          sessions.map((session) => {
            const isActive = activeSessionId === session.session_id;
            return (
              <div 
                key={session.session_id}
                className={`group flex items-center justify-between rounded-xl px-3 py-2.5 text-sm font-medium transition-all cursor-pointer ${
                  isActive 
                    ? 'bg-zinc-900 text-zinc-100 border border-zinc-800' 
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/40'
                }`}
                onClick={() => onSelectSession(session.session_id)}
              >
                <div className="flex items-center gap-2.5 min-w-0 flex-1">
                  <MessageSquare className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-indigo-400' : 'text-zinc-500'}`} />
                  <span className="truncate pr-1 text-xs">
                    {session.title || 'Untitled Session'}
                  </span>
                </div>
                
                {/* Delete Button (visible on hover) */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(session.session_id);
                  }}
                  className="opacity-0 group-hover:opacity-100 hover:text-rose-500 p-1 transition-all rounded"
                  title="Delete chat"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-zinc-900 space-y-4">
        
        {/* Status */}
        <div className="flex items-center justify-between px-2.5 py-2 bg-zinc-900/40 rounded-xl border border-zinc-900/80">
          <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider flex items-center gap-1.5">
            {backendOnline ? <Wifi className="w-3.5 h-3.5 text-emerald-500" /> : <WifiOff className="w-3.5 h-3.5 text-rose-500" />}
            Status
          </span>
          <span className={`text-[10px] font-bold ${backendOnline ? 'text-emerald-400' : 'text-rose-400'}`}>
            {backendOnline ? 'ONLINE' : 'OFFLINE'}
          </span>
        </div>

        {/* Clear memories */}
        <button
          onClick={handleClearCache}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg border border-zinc-900 bg-zinc-950 hover:bg-rose-950/20 hover:text-rose-400 hover:border-rose-900/40 text-zinc-500 text-xs font-semibold transition-all duration-150"
          title="Wipe cached weather lookups"
        >
          <Database className="w-3.5 h-3.5" />
          Reset Memory Cache
        </button>

        {/* Version */}
        <div className="text-center">
          <span className="text-[9px] text-zinc-700 font-bold tracking-wider uppercase">
            Aura Minimal v1.0
          </span>
        </div>

      </div>

    </aside>
  );
};

export default Sidebar;
