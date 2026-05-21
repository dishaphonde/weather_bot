import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes import chat
from services.memory_service import memory_service
from utils.logger import logger

app = FastAPI(
    title="Minimal AI Weather Chatbot API",
    description="Backend API powering the Aura AI Weather Chatbot.",
    version="1.0.0"
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:5174", 
        "http://127.0.0.1:5173", 
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Timing middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(f"Method: {request.method} Path: {request.url.path} Status: {response.status_code} Duration: {duration:.4f}s")
    return response

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on path {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Server error: {str(exc)}"}
    )

# Include routes
app.include_router(chat.router)

# Clear vector and weather memory cache
@app.delete("/memory/clear")
async def clear_all_memories():
    try:
        success = memory_service.clear_all_memories()
        return {"success": success, "message": "All cached weather and vector memories cleared"}
    except Exception as e:
        logger.error(f"Error clearing memories: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to clear memory: {str(e)}"}
        )

@app.get("/")
async def root():
    return {
        "status": "online",
        "agent": "Aura AI Weather Chatbot Backend",
        "endpoints": {
            "stream_chat": "POST /chat/stream",
            "get_sessions": "GET /chat/sessions",
            "get_history": "GET /chat/history/{session_id}",
            "delete_session": "DELETE /chat/history/{session_id}",
            "clear_all_sessions": "DELETE /chat/sessions",
            "clear_memories": "DELETE /memory/clear"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
