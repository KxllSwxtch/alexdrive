from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 3001
    cors_origins: str = "http://localhost:3000"
    namsuwon_base_url: str = "https://cars.namsuwon.com"
    proxy_url: str = ""
    admin_secret: str = ""
    min_request_interval: float = 0.5

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [s.strip() for s in self.cors_origins.split(",")]


settings = Settings()
