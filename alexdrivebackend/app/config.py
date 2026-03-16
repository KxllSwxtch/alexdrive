from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 3001
    cors_origins: str = "http://localhost:3000"
    jenya_base_url: str = "https://m.jenya.co.kr"
    jenya_carcode_url: str = "https://m.jenya.co.kr/as5/script/carcode2_en.js"
    proxy_url: str = ""
    admin_secret: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [s.strip() for s in self.cors_origins.split(",")]


settings = Settings()
