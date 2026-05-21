import json
import time
import re
from typing import Generator, List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from services.memory_service import memory_service
from services.weather_service import weather_service
from utils.config import config
from utils.logger import logger

router = APIRouter(prefix="/chat", tags=["Chat"])

# Schemas
class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: str = "default_user"

class ChatHistoryResponse(BaseModel):
    role: str
    content: str
    timestamp: str

class SessionResponse(BaseModel):
    session_id: str
    title: str
    timestamp: str

# Initialize LangChain ChatGroq models
llm = ChatGroq(
    groq_api_key=config.GROQ_API_KEY,
    model_name="llama-3.3-70b-versatile",
    temperature=0.4
)

extractor_llm = ChatGroq(
    groq_api_key=config.GROQ_API_KEY,
    model_name="llama-3.3-70b-versatile",
    temperature=0.0
)

def extract_city_from_query(text: str) -> Optional[str]:
    """
    Extracts a single city name from the query.
    Uses LLM parsing with JSON instructions, falling back to basic regex.
    """
    system_prompt = (
        "You are an assistant that extracts city names from user queries for weather lookups.\n"
        "Identify the primary city mentioned in the user query. Return a JSON object with a single field 'city' containing the city name in title case.\n"
        "If no city is mentioned, return {\"city\": null}.\n"
        "Do not explain, do not add markdown, just return the JSON object."
    )
    try:
        response = extractor_llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Query: {text}")
        ])
        content = response.content.strip()
        
        # Parse JSON
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            content = match.group(0)
            
        data = json.loads(content)
        city = data.get("city")
        if city:
            return str(city).strip().title()
    except Exception as e:
        logger.error(f"LLM city extraction failed: {e}")
        
    # Regex fallback for common patterns (e.g., "in Pune", "weather in Goa", "for Delhi")
    patterns = [
        r"(?:weather|temp|forecast|temperature|climate|rain)\s+(?:in|for|at|of)\s+([a-zA-Z\s]+)",
        r"(?:in|at|for)\s+([a-zA-Z\s]+)\??$"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # Split off trailing punctuation or words
            candidate = re.split(r'\s+(?:today|tomorrow|this|next|is|are|the|forecast)\b', candidate, flags=re.IGNORECASE)[0]
            return candidate.title()
            
    return None

@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """
    Streams chatbot response. Checks weather memory cache first before calling
    API and generating a personalized report.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    def stream_generator() -> Generator[str, None, None]:
        try:
            # 1. Save user query to history
            memory_service.save_chat_message(request.session_id, "user", request.message)

            # 2. Extract city name
            city = extract_city_from_query(request.message)
            
            # 3. Memory Retrieval flow
            if city:
                logger.info(f"City '{city}' detected in user query.")
                cached_memory = memory_service.get_weather_memory(city)
                
                if cached_memory:
                    logger.info(f"Found weather cache for '{city}' in SQLite memory.")
                    stored_response = cached_memory["ai_response"]
                    full_formatted = f"[Retrieved from Memory]\n\n{stored_response}"
                    
                    # Yield character by character with minor delay to simulate typing
                    # (Chunking by words/tokens is much faster but still looks smooth)
                    words = full_formatted.split(" ")
                    for i, word in enumerate(words):
                        yield word + (" " if i < len(words) - 1 else "")
                        time.sleep(0.01) # 10ms delay for visual flow
                    
                    # Save AI response to session history
                    memory_service.save_chat_message(request.session_id, "assistant", full_formatted)
                    return
                else:
                    logger.info(f"No weather cache found for '{city}'. Fetching live data...")
                    weather_data = weather_service.get_weather_data(city)
                    
                    if "error" in weather_data:
                        err_msg = f"Could not retrieve weather details for **{city}**: {weather_data['error']}"
                        yield err_msg
                        memory_service.save_chat_message(request.session_id, "assistant", err_msg)
                        return

                    # Construct detailed weather context
                    curr = weather_data["current"]
                    forecast_str = ""
                    for entry in weather_data.get("forecast", [])[:5]:
                        time_str = entry["datetime_str"].split(" ")[1][:5]
                        forecast_str += f"- Time {time_str}: {entry['temperature']}°C, {entry['description']}, Rain prob: {entry['rain_prob']}%\n"
                    
                    weather_context = (
                        f"Weather Report for {weather_data['city']}, {weather_data['country']}:\n"
                        f"- Temperature: {curr['temperature']}°C (Feels like {curr['feels_like']}°C)\n"
                        f"- Conditions: {curr['description'].title()}\n"
                        f"- Humidity: {curr['humidity']}%, Wind Speed: {curr['wind_speed']} m/s\n"
                        f"- Air Quality Index (AQI): {weather_data.get('aqi')} (1=Good, 5=Hazardous)\n"
                        f"- Next 15 Hours Forecast:\n{forecast_str}"
                    )
            else:
                logger.info("No city detected in query. Proceeding with general AI conversation.")
                weather_context = "No specific city weather data requested."

            # Construct system prompt
            system_prompt = (
                "You are 'Aura', a helpful, personal AI Weather Agent.\n"
                "Your objective is to deliver beautiful, concise, and highly personalized weather descriptions, clothing tips, and activity recommendations based on the provided live weather conditions.\n\n"
                "--- LIVE WEATHER DATA ---\n"
                f"{weather_context}\n\n"
                "--- RULES ---\n"
                "1. Keep responses clear, friendly, and structured. Use Markdown bullet points.\n"
                "2. Provide direct clothing advice (e.g., recommend coats, boots, umbrellas, or sunglasses) based on the humidity, temperature, and precipitation forecasts.\n"
                "3. If air quality (AQI) is poor (AQI >= 4), warn sensitive groups.\n"
                "4. If no weather data was requested, answer conversational queries naturally in a friendly tone while staying in your weather agent persona.\n"
                "5. Limit explanations to what is necessary. Avoid long paragraphs; use lists."
            )

            # Retrieve recent conversation history for flow
            session_history = memory_service.get_chat_history(request.session_id, limit=8)
            messages = [SystemMessage(content=system_prompt)]
            
            # Add past messages (skipping current user message which is appended last)
            # Skip the very last user message from SQLite since we add it explicitly to the LangChain call
            history_to_append = session_history[:-1] if session_history else []
            for msg in history_to_append:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

            messages.append(HumanMessage(content=request.message))

            # Run streaming completion
            full_response = ""
            for chunk in llm.stream(messages):
                chunk_text = chunk.content
                if chunk_text:
                    full_response += chunk_text
                    yield chunk_text

            # Post-completion tasks
            if full_response.strip():
                # Save response to history
                memory_service.save_chat_message(request.session_id, "assistant", full_response)
                
                # If city weather was looked up, cache it under that city
                if city and "error" not in weather_data:
                    memory_service.save_weather_memory(city, request.message, full_response)
                    logger.info(f"Cached weather response for '{city}' in database.")
                    
        except Exception as e:
            logger.error(f"Error in stream generator: {e}")
            yield f"\n\n[System Error: {str(e)}]"

    return StreamingResponse(stream_generator(), media_type="text/plain")

@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions():
    """Retrieves all chat sessions for the left sidebar."""
    try:
        return memory_service.get_sessions()
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{session_id}", response_model=List[ChatHistoryResponse])
async def get_history(session_id: str):
    """Loads message history for a specific session."""
    try:
        history = memory_service.get_chat_history(session_id)
        return history
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history/{session_id}")
async def delete_session(session_id: str):
    """Deletes a specific chat session."""
    try:
        success = memory_service.delete_session(session_id)
        return {"success": success, "message": "Session deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions")
async def clear_all_sessions():
    """Clears all sessions and history."""
    try:
        success = memory_service.delete_all_sessions()
        return {"success": success, "message": "All conversations cleared"}
    except Exception as e:
        logger.error(f"Error clearing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
