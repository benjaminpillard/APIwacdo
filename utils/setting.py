from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    DATABASE_URL: str
    CORS_ORIGINS: str = ""
    # Durée de validité d'un token de connexion
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # Nombre maximal de tentatives de connexion par adresse IP (anti brute-force)
    LOGIN_RATE_LIMIT: str = "5/minute"

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.CORS_ORIGINS.strip():
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()  # pyright: ignore[reportCallIssue]