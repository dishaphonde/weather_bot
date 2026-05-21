# AI Weather Agent

A full-stack AI-powered Weather Agent built with React, Vite, FastAPI, and Groq (Llama-3). It features tool-calling capabilities to fetch live weather data and present it in a natural, conversational format.

## Features
- **Frontend**: React + Vite with a beautiful, modern, dark-mode glassmorphism UI.
- **Backend**: FastAPI with async endpoints and proper CORS handling.
- **LLM Engine**: Groq SDK using the `llama-3.3-70b-versatile` model for lightning-fast responses.
- **Tool Calling**: Native function calling to fetch real-time weather from OpenWeatherMap.

## Project Structure
- `backend/`: FastAPI application, agent logic, and tool definitions.
- `frontend/`: Vite + React application, CSS, and UI components.

## Prerequisites
- Python 3.9+
- Node.js 18+

## Setup Instructions

### 1. OpenWeatherMap API Key
1. Go to [OpenWeatherMap](https://openweathermap.org/) and create a free account.
2. Navigate to your dashboard and go to the "API keys" tab.
3. Generate a new key and copy it.

### 2. Backend Setup
Open a terminal and navigate to the project root:
```bash
cd backend
```

Create a virtual environment (optional but recommended):
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Set up environment variables:
Edit the `.env` file in the `backend` directory (or copy `.env.example` to `.env`) and add your API keys:
```env
GROQ_API_KEY=your_groq_key_here
WEATHER_API_KEY=your_openweathermap_api_key_here
```

Run the backend server:
```bash
uvicorn main:app --reload
```
The FastAPI backend will start on `http://localhost:8000`.

### 3. Frontend Setup
Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
```

Install dependencies:
```bash
npm install
```

Start the Vite development server:
```bash
npm run dev
```
The React frontend will start on `http://localhost:5173`.

## Usage
1. Open your browser and go to the frontend URL (e.g., `http://localhost:5173`).
2. Type a message like "What is the temperature in Pune?" or "How's the weather in Mumbai?"
3. The AI agent will automatically detect the intent, call the OpenWeatherMap tool, and reply with human-friendly weather data!
