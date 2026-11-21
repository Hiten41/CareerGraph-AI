from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://careergraph:localdev@localhost:5432/careergraph"
    web_origin: str = "http://localhost:3000"
    cookie_secure: bool = False
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = ""
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    upload_limit: int = 5_000_000
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
