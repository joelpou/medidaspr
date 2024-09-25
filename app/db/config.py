from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    db_url: str = Field('postgresql://medidaspr:medidaspr@db:5432/medidaspr', env='DATABASE_URL')
    # db_url: str = Field(..., env='DATABASE_URL')

settings = Settings()
