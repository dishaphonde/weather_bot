import os
import sys
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "data/weather_agent.db")
    CHROMA_PATH = os.getenv("CHROMA_PATH", "data/chromadb")

    # Ensure data directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    os.makedirs(CHROMA_PATH, exist_ok=True)

    @classmethod
    def validate(cls):
        """Validates that required environment variables are set."""
        missing = []
        if not cls.GROQ_API_KEY or cls.GROQ_API_KEY == "your_groq_api_key_here":
            missing.append("GROQ_API_KEY")
        if not cls.WEATHER_API_KEY or cls.WEATHER_API_KEY == "your_openweathermap_api_key_here":
            # Weather API is optional — mock data will be used as fallback
            print("[WARNING] WEATHER_API_KEY is not configured. Mock weather data will be used.")
        if missing:
            print(f"[ERROR] Missing required environment variables: {', '.join(missing)}")
            print("Please copy backend/.env.example to backend/.env and fill in your API keys.")
            sys.exit(1)

config = Config()
config.validate()
