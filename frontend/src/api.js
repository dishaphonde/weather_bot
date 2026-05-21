import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
});

// Chat Sessions API
export const getSessions = async () => {
  const response = await api.get('/chat/sessions');
  return response.data;
};

export const deleteSession = async (sessionId) => {
  const response = await api.delete(`/chat/history/${sessionId}`);
  return response.data;
};

export const clearAllSessions = async () => {
  const response = await api.delete('/chat/sessions');
  return response.data;
};

// Chat History API
export const getChatHistory = async (sessionId) => {
  const response = await api.get(`/chat/history/${sessionId}`);
  return response.data;
};

// Memory Cache API
export const clearMemoryCache = async () => {
  const response = await api.delete('/memory/clear');
  return response.data;
};

// Streaming Chat API (Native Fetch to support chunk streams)
export const streamChat = async (message, sessionId, onChunk, onDone, onError) => {
  try {
    const response = await fetch(`${BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        user_id: 'default_user'
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let done = false;
    let accumulatedText = '';

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      if (value) {
        const chunk = decoder.decode(value, { stream: !done });
        accumulatedText += chunk;
        onChunk(chunk, accumulatedText);
      }
    }
    
    if (onDone) onDone(accumulatedText);
  } catch (error) {
    console.error('Error in streaming chat:', error);
    if (onError) onError(error);
  }
};
