import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY          = os.environ.get("SECRET_KEY", "troque-isso-em-producao")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Postgres: postgresql://usuario:senha@host:porta/nome_db
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:04062019@localhost:5432/helpage"
    )

    # Upload de fotos (idoso)
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024   # 4 MB
    UPLOAD_FOLDER      = os.path.join(os.path.dirname(__file__), "app", "static", "uploads")


class DevelopmentConfig(Config):
    DEBUG        = True
    SQLALCHEMY_ECHO = True   # loga todas as queries SQL no terminal


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}