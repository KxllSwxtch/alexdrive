from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 3001
    cors_origins: str = "http://localhost:3000"
    carmanager_username: str = ""
    carmanager_password: str = ""
    carmanager_base_url: str = "https://www.carmanager.co.kr"
    admin_secret: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [s.strip() for s in self.cors_origins.split(",")]


settings = Settings()
