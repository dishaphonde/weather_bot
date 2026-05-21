import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatPage from './pages/ChatPage';
import { 
  getSessions, 
  getChatHistory, 
  deleteSession, 
  clearAllSessions, 
  streamChat 
} from './api';

const generateSessionId = () => {
  return 'session_' + Math.random().toString(36).substring(2, 11);
};

function App() {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);

  // Check backend health and fetch sessions on load
  useEffect(() => {
    const initApp = async () => {
      try {
        const response = await fetch('http://localhost:8000/');
        if (response.ok) {
          setBackendOnline(true);
          await loadSessionsList(true); // Load sessions and select latest
        } else {
          setBackendOnline(false);
        }
      } catch (err) {
        console.error("Backend offline:", err);
        setBackendOnline(false);
      }
    };

    initApp();
  }, []);

  // Fetch session history list
  const loadSessionsList = async (shouldSelectLatest = false) => {
    try {
      const list = await getSessions();
      setSessions(list);
      
      if (shouldSelectLatest) {
        if (list.length > 0) {
          const latestSessionId = list[0].session_id;
          setActiveSessionId(latestSessionId);
          await loadSessionHistory(latestSessionId);
        } else {
          // If no sessions exist, initiate a clean one
          handleNewChat();
        }
      }
    } catch (err) {
      console.error("Failed to load sessions:", err);
    }
  };

  // Load message logs for selected session
  const loadSessionHistory = async (sessionId) => {
    try {
      const history = await getChatHistory(sessionId);
      // Map schema: { role: 'user'|'assistant', content: string, timestamp: string }
      // to UI schema: { sender: 'user'|'assistant', text: string, timestamp: string }
      const formatted = history.map(msg => ({
        sender: msg.role,
        text: msg.content,
        timestamp: msg.timestamp
      }));
      setMessages(formatted);
    } catch (err) {
      console.error("Error loading chat history:", err);
    }
  };

  const handleSelectSession = async (sessionId) => {
    setActiveSessionId(sessionId);
    await loadSessionHistory(sessionId);
  };

  const handleNewChat = () => {
    const newId = generateSessionId();
    setActiveSessionId(newId);
    setMessages([]);
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await deleteSession(sessionId);
      const remainingSessions = sessions.filter(s => s.session_id !== sessionId);
      setSessions(remainingSessions);
      
      // If we deleted the active session, switch to the next available or start new
      if (activeSessionId === sessionId) {
        if (remainingSessions.length > 0) {
          const nextActiveId = remainingSessions[0].session_id;
          setActiveSessionId(nextActiveId);
          await loadSessionHistory(nextActiveId);
        } else {
          handleNewChat();
        }
      }
    } catch (err) {
      console.error("Error deleting session:", err);
    }
  };

  const handleSendMessage = async (text) => {
    if (!text.trim() || loading) return;

    setLoading(true);
    const timestamp = new Date().toISOString();

    // 1. Add user message locally
    const updatedMessages = [...messages, { sender: 'user', text, timestamp }];
    setMessages(updatedMessages);

    // 2. Add empty streaming placeholder for AI response
    setMessages(prev => [...prev, { sender: 'assistant', text: '', timestamp }]);

    try {
      await streamChat(
        text,
        activeSessionId,
        (chunk, accumulated) => {
          // Streaming chunk update callback
          setMessages(prev => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.sender === 'assistant') {
              last.text = accumulated;
            }
            return updated;
          });
        },
        async (finalResponse) => {
          // Done callback
          setLoading(false);
          // Refresh sessions list in sidebar to capture title changes
          await loadSessionsList(false);
        },
        (error) => {
          // Error callback
          setLoading(false);
          setMessages(prev => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.sender === 'assistant') {
              last.text = "Error receiving streaming response. Please check your backend connection.";
            }
            return updated;
          });
        }
      );
    } catch (err) {
      console.error("Failed to stream chat:", err);
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen bg-zinc-950 text-zinc-100 overflow-hidden font-sans antialiased">
      {/* Sidebar Navigation */}
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        backendOnline={backendOnline}
      />
      
      {/* Main Chat Display Page */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        <ChatPage
          messages={messages}
          onSendMessage={handleSendMessage}
          loading={loading}
          activeSessionId={activeSessionId}
        />
      </main>
    </div>
  );
}

export default App;
