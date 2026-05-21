import React, { useState } from 'react';
import { User, CloudSun, Copy, Check, Info } from 'lucide-react';
import MarkdownRenderer from './MarkdownRenderer';

const MessageBubble = ({ message, sender, timestamp }) => {
  const isUser = sender === 'user';
  const [copied, setCopied] = useState(false);

  // Check if message is fetched from database cache
  const isFromMemory = message.includes('[Retrieved from Memory]');
  // Strip out the tag for rendering
  const cleanMessage = message.replace('[Retrieved from Memory]', '').trim();

  const copyToClipboard = () => {
    navigator.clipboard.writeText(cleanMessage);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formattedTime = timestamp 
    ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <div className={`w-full py-5 border-b border-zinc-900/50 flex justify-center ${isUser ? 'bg-transparent' : 'bg-zinc-900/20'}`}>
      <div className="w-full max-w-3xl px-4 flex gap-4 md:gap-6">
        
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center border shadow-sm ${
          isUser 
            ? 'bg-zinc-800 border-zinc-700 text-zinc-300' 
            : 'bg-indigo-950/60 border-indigo-800/80 text-indigo-400'
        }`}>
          {isUser ? <User className="w-4.5 h-4.5" /> : <CloudSun className="w-4.5 h-4.5" />}
        </div>

        {/* Content */}
        <div className="flex-1 flex flex-col min-w-0">
          
          {/* Header */}
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs font-semibold text-zinc-400">
              {isUser ? 'You' : 'Aura'}
            </span>
            <span className="text-[10px] text-zinc-500 font-medium">
              {formattedTime}
            </span>
            
            {/* Memory Recall Badge */}
            {!isUser && isFromMemory && (
              <span className="flex items-center gap-1 text-[9px] font-bold bg-indigo-950/40 text-indigo-400 px-1.5 py-0.5 rounded-full border border-indigo-900/30 animate-pulse">
                <Info className="w-2.5 h-2.5" />
                Memory Recall
              </span>
            )}
          </div>

          {/* Message Text */}
          <div className="text-zinc-200 text-sm md:text-base leading-relaxed break-words">
            {isUser ? (
              <p className="whitespace-pre-wrap font-medium">{cleanMessage}</p>
            ) : (
              <MarkdownRenderer content={cleanMessage} />
            )}
          </div>

          {/* Action Row */}
          {!isUser && cleanMessage && (
            <div className="mt-3 flex gap-2">
              <button 
                onClick={copyToClipboard}
                title="Copy response to clipboard"
                className="p-1 rounded text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50 transition-all flex items-center gap-1.5 text-xs font-semibold"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-500" />
                    <span className="text-emerald-500 text-[10px]">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span className="text-[10px] hidden sm:inline">Copy</span>
                  </>
                )}
              </button>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
