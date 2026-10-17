from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_base_url: str = ""
    llm_model: str = "gemma4:cloud"
    ollama_available_models: str = "gemma4:cloud,gpt-oss:120b,nemotron-3-ultra"
    ollama_api_key: str = ""

    database_url: str = "sqlite:///./data/secure_health.db"
    chroma_persist_dir: str = "./rag_index"
    literatura_path: str = "./data/literatura"

    clinical_alerts_enabled: bool = True

    @property
    def api_keys(self) -> list[str]:
        return [k.strip() for k in self.ollama_api_key.split(",") if k.strip()]

    @property
    def available_models(self) -> list[str]:
        return [m.strip() for m in self.ollama_available_models.split(",") if m.strip()]

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_base_url and self.api_keys)


settings = Settings()
