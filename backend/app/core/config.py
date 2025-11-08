from pydantic import BaseModel
import os


class Settings(BaseModel):
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./albumduel.db")
    spotify_client_id: str | None = os.getenv("SPOTIFY_CLIENT_ID")
    spotify_client_secret: str | None = os.getenv("SPOTIFY_CLIENT_SECRET")
    spotify_redirect_uri: str | None = os.getenv("SPOTIFY_REDIRECT_URI")
    lastfm_api_key: str | None = os.getenv("LASTFM_API_KEY")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me")
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")


settings = Settings()
