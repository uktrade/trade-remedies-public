from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings


class VCAPServices(BaseModel):
    model_config = ConfigDict(extra="ignore")

    postgres: list[dict[str, Any]] = Field(alias="postgres", default=[])
    redis: list[dict[str, Any]] = Field(alias="redis", default=[])
    aws_s3_bucket: list[dict[str, Any]] = Field(alias="aws-s3-bucket", default=[])
    opensearch: list[dict[str, Any]] = Field(alias="opensearch", default=[])


class CloudFoundrySettings(BaseSettings):
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "local"
    DJANGO_SECRET_KEY: str = ""
    DEBUG: bool = True
    ALLOWED_HOSTS: str = ""
    ORGANISATION_NAME: str = "Organisation name placeholder"
    ORGANISATION_INITIALISM: str = "Organisation initialism placeholder"
    BASIC_AUTH_USER: dict = {}
    VCAP_SERVICES: Optional[VCAPServices] = {}
    REDIS_DATABASE_NUMBER: int = 2
    REDIS_BASE_URL: str = "redis://redis:6379"
    SECURE_COOKIE: bool = False
    SESSION_LENGTH_MINUTES: int = 30
    SECURE_CSRF_COOKIE: bool = False
    CSRF_COOKIE_HTTPONLY: bool = False
    USE_2FA: bool = True
    VERIFY_EMAIL: bool = True
    GA_TAG_MANAGER_ID: str = "GTM-XXXXXX"
    API_BASE_URL: str = "http://localhost:8000"
    HEALTH_CHECK_TOKEN: str = "health-check-token"
    ENVIRONMENT_KEY: str = "PUB-ENV"
    S3_STORAGE_KEY: Optional[str] = None
    S3_STORAGE_SECRET: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = None
    AWS_STORAGE_BUCKET_NAME: Optional[str] = None
    AWS_REGION: str = "eu-west-1"
    CLAM_AV_USERNAME: Optional[str] = None
    CLAM_AV_PASSWORD: Optional[str] = None
    CLAM_AV_DOMAIN: Optional[str] = None
    USE_CLAM_AV: bool = True
    ROOT_LOG_LEVEL: str = "INFO"
    DJANGO_LOG_LEVEL: str = "INFO"
    DJANGO_SERVER_LOG_LEVEL: str = "INFO"
    DJANGO_REQUEST_LOG_LEVEL: str = "INFO"
    DEFAULT_CHUNK_SIZE: int = 33554432
    FILE_MAX_SIZE_BYTES: int = 31457280

    def get_allowed_hosts(self) -> list[str]:
        return self.ALLOWED_HOSTS.split(",") if self.ALLOWED_HOSTS else ["localhost"]

    def get_s3_bucket_config(self) -> dict:
        """Return s3 bucket config that matches keys used in CF"""

        return {
            "aws_region": self.AWS_REGION,
            "bucket_name": self.S3_BUCKET_NAME or self.AWS_STORAGE_BUCKET_NAME or "",
            "storage_secret": self.S3_STORAGE_SECRET,
            "storage_key": self.S3_STORAGE_KEY,
        }
