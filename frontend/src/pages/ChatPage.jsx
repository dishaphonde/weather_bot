import React, { useEffect, useRef } from 'react';
import MessageBubble from '../components/MessageBubble';
import ChatInput from '../components/ChatInput';
import { CloudLightning, Sparkles } from 'lucide-react';

const ChatPage = ({ 
  messages, 
  onSendMessage, 
  loading, 
  activeSessionId 
}) => {
  const messagesEndRef = useRef(null);

  // Auto-scroll on new messages or typing state changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const suggestions = [
    { text: "What is the weather in Pune?", label: "Pune Weather" },
    { text: "Is it raining in Goa? Recommend clothes.", label: "Goa Travel Forecast" },
    { text: "Check Delhi climate and air quality today.", label: "Delhi AQI & Weather" },
    { text: "Explain how rain forms.", label: "General Rain Science" }
  ];

  return (
    <div className="flex-1 flex flex-col h-full bg-zinc-950 text-zinc-100 overflow-hidden relative">
      
      {/* Top Header */}
      <div className="h-16 border-b border-zinc-900 bg-zinc-950/80 backdrop-blur-md px-6 flex items-center justify-between z-10 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-bold text-zinc-400">
            Aura Chat Assistant
          </span>
        </div>
      </div>

      {/* Messages scrolling container */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {messages.length === 0 ? (
          <div className="min-h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto px-6 py-12">
            
            {/* Logo */}
            <div className="w-14 h-14 rounded-2xl bg-indigo-950/40 border border-indigo-900/30 flex items-center justify-center mb-6 shadow-xl shadow-indigo-950/20 animate-bounce">
              <CloudLightning className="w-7 h-7 text-indigo-400" />
            </div>
            
            <h1 className="text-2xl font-bold tracking-tight text-zinc-200">
              How can I help you today?
            </h1>
            <p className="text-zinc-500 text-sm mt-2 leading-relaxed">
              Ask me about real-time weather conditions, multi-day forecasts, clothing recommendations, or start a general conversation. All weather queries are cached in memory.
            </p>

            {/* Suggestions list */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full mt-8">
              {suggestions.map((sug, idx) => (
                <button
                  key={idx}
                  onClick={() => onSendMessage(sug.text)}
                  className="bg-zinc-900/40 hover:bg-zinc-900 border border-zinc-900 hover:border-zinc-800 rounded-xl p-3.5 text-left text-xs font-semibold text-zinc-400 hover:text-zinc-200 transition-all duration-150"
                >
                  <span className="block text-[10px] uppercase font-bold tracking-wider text-indigo-400 mb-1">
                    {sug.label}
                  </span>
                  {sug.text}
                </button>
              ))}
            </div>

          </div>
        ) : (
          <div className="flex flex-col">
            {messages.map((msg, idx) => (
              <MessageBubble
                key={idx}
                message={msg.text}
                sender={msg.sender}
                timestamp={msg.timestamp}
              />
            ))}
            
            {/* Real-time Loader animation */}
            {loading && messages[messages.length - 1]?.sender === 'user' && (
              <div className="w-full py-5 bg-zinc-900/20 border-b border-zinc-900/50 flex justify-center">
                <div className="w-full max-w-3xl px-4 flex gap-4 md:gap-6">
                  <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-indigo-950/60 border border-indigo-800/80 text-indigo-400 flex items-center justify-center">
                    <CloudLightning className="w-4.5 h-4.5 animate-pulse" />
                  </div>
                  <div className="flex flex-col pt-1.5 gap-1">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-semibold text-zinc-400">Aura is thinking...</span>
                    </div>
                    {/* Bouncing Dots typing animation */}
                    <div className="flex gap-1 mt-2.5 items-center">
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce [animation-delay:-0.3s]" />
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce [animation-delay:-0.15s]" />
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce" />
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} className="h-6" />
          </div>
        )}
      </div>

      {/* Fixed Bottom Input Area */}
      <ChatInput onSend={onSendMessage} loading={loading} />

    </div>
  );
};

export default ChatPage;
