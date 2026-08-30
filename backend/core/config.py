from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    discord_token: str
    database_url: str
    discord_client_id: str = ""
    discord_client_secret: str = ""
    app_url: str
    api_url: str
    public_base_url: str
    frontend_url: str
    jwt_secret: str
    admin_username: str
    admin_password: str
    discord_reviewer_role: str = "Reviewer"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
