import React, { useState, useEffect, useRef } from 'react';
import { Send, Mic, MicOff } from 'lucide-react';

const ChatInput = ({ onSend, loading }) => {
  const [inputValue, setInputValue] = useState('');
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);

  // Setup browser Web Speech Recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = false;
      rec.lang = 'en-US';

      rec.onresult = (event) => {
        const text = event.results[0][0].transcript;
        setInputValue(prev => prev + (prev ? ' ' : '') + text);
        setIsListening(false);
      };

      rec.onerror = (e) => {
        console.error("Speech recognition error:", e);
        setIsListening(false);
      };

      rec.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = rec;
    }
  }, []);

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert("Speech recognition is not supported in this browser. Please try Chrome, Edge, or Safari.");
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      setIsListening(true);
      recognitionRef.current.start();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;
    onSend(inputValue.trim());
    setInputValue('');
  };

  return (
    <div className="w-full bg-zinc-950/80 border-t border-zinc-900/60 p-4 pb-6 flex-shrink-0 flex justify-center backdrop-blur-md">
      <form onSubmit={handleSubmit} className="w-full max-w-3xl flex gap-2 relative">
        
        {/* Voice Input Mic */}
        <button
          type="button"
          onClick={toggleListening}
          title={isListening ? "Listening... click to stop" : "Start Voice Input"}
          className={`p-3 rounded-xl border flex items-center justify-center transition-all ${
            isListening 
              ? 'bg-rose-500/20 border-rose-500 text-rose-400 animate-pulse' 
              : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-indigo-400 hover:bg-zinc-800/80'
          }`}
        >
          {isListening ? <MicOff className="w-4.5 h-4.5" /> : <Mic className="w-4.5 h-4.5" />}
        </button>

        {/* Text Input */}
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={isListening ? "Listening to your voice..." : "Ask Aura about any city weather (e.g., Goa, Pune)..."}
          className="flex-1 bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-900/50 transition-all font-medium"
          disabled={loading}
        />

        {/* Send Button */}
        <button
          type="submit"
          disabled={!inputValue.trim() || loading}
          className="p-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-indigo-900/20 flex items-center justify-center"
        >
          <Send className="w-4 h-4" />
        </button>

        {isListening && (
          <div className="absolute left-4 -top-12 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 flex items-center gap-2 shadow-lg animate-bounce text-xs font-bold text-zinc-400">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping" />
            Listening...
          </div>
        )}
      </form>
    </div>
  );
};

export default ChatInput;
