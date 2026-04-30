"""Local config - runs on developer machine."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class LocalSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    env: str = "local"
    service_name: str = "summerization-ai-agent"
    port: int = 
    grpc_port: int = 
    log_level: str = "debug"
    debug: bool = True

    # LLM provider
    intent_router_provider: str = ""

    # Vertex AI / Gemini
    google_application_credentials: str = ""
    vertex_ai_project_id: str = ""
    vertex_ai_location: str = ""
    gemini_model: str = ""
    gcp_private_key_id: str = ""
    gcp_private_key: str = ""
    gcp_client_email: str = ""
    gcp_client_id: str = ""

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = ""

    # Summarization engine
    summarization_max_input_tokens: int = 32000
    summarization_max_output_tokens: int = 2048
    summarization_temperature: float = 0.3
    narrative_temperature: float = 0.5

    # Database
    db_username: str = ""
    db_password: str = ""
    db_host: str = ""
    db_port: int = 
    db_name: str = ""
    db_schema: str = ""
    db_pool_min_size: int = 1
    db_pool_max_size: int = 5

    # Redis
    redis_host: str = ""
    redis_port: int = 
    redis_password: str = ""

    # Auth
    auth_enabled: bool = False
    onified_jwt_secret_key: str = ""
    jwt_algorithm: str = ""

    # Langfuse observability
    langfuse_enabled: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = ""

    @property
    def db_dsn(self) -> str:
        host = self.db_host.removeprefix("postgresql://")
        return f"postgresql://{self.db_username}:{self.db_password}@{host}:{self.db_port}/{self.db_name}"

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}"
        return f"redis://{self.redis_host}:{self.redis_port}"


settings = LocalSettings()
