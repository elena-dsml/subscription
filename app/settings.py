from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', extra='allow', env_prefix='subscription_api_'
    )
    project_name: str = Field(default="Subscription Service")
    bill_api_base_url: str = Field(default="http://bill-api-nginx:8000")
    cors_origins: list[str] = ["*"]
    auth_api_access_token_check_url: str = Field(
        default="http://auth-api-nginx:8000/api/v1/auth/check_access_token"
    )
    secret_key: str = Field(default="secretkey123")
    db_echo: bool = Field(default=False)


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', extra='allow', env_prefix='subscription_pg_'
    )

    host: str = Field(default='127.0.0.1')
    port: int = Field(default=5432)
    user: str
    password: str
    db: str

    def get_url(self, driver: str | None = None, db: str | None = None) -> str:
        scheme = f'postgresql{f"+{driver}" if driver else ""}'
        return f"{scheme}://{self.user}:{self.password}@{self.host}:{self.port}/{db or self.db}"


class KafkaSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', extra='allow', env_prefix='subscription_kafka_'
    )

    bootstrap_servers: str = Field(default='localhost:19092')


settings = Settings()       # type: ignore
pg_settings = PostgresSettings()  # type: ignore
kafka_settings = KafkaSettings()  # type: ignore
