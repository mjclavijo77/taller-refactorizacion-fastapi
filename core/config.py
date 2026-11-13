from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise E-Commerce API"
    API_V1_STR: str = "/api/v1"
    STRIPE_API_KEY: str = "sk_test_mock_12345"
    JWT_SECRET: str = "SUPER_SECRET_KEY_FOR_LAST_SEMESTER_STUDENTS"

    class Config:
        case_sensitive = True

settings = Settings()