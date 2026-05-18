from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

from config import config_map

# ── extensões (instanciadas aqui, inicializadas no factory) ──
db           = SQLAlchemy()
migrate      = Migrate()
login_manager = LoginManager()

login_manager.login_view     = "auth.login"
login_manager.login_message  = "Faça login para continuar."
login_manager.login_message_category = "warning"


def create_app(env: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_map[env])

    # ── inicializa extensões ──────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # ── importa models para o Migrate detectar ────────────────
    with app.app_context():
        from app import models  # noqa: F401

    # ── registra blueprints ───────────────────────────────────
    from app.routes.auth         import auth_bp
    from app.routes.dashboard    import dashboard_bp
    from app.routes.medicamentos import medicamentos_bp
    from app.routes.turnos       import turnos_bp
    from app.routes.registros    import registros_bp
    from app.routes.idosos       import idosos_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(medicamentos_bp, url_prefix="/medicamentos")
    app.register_blueprint(turnos_bp,       url_prefix="/turnos")
    app.register_blueprint(registros_bp,    url_prefix="/registros")
    app.register_blueprint(idosos_bp,       url_prefix="/idosos")

    return app


# ── user loader exigido pelo Flask-Login ─────────────────────
@login_manager.user_loader
def load_user(user_id: str):
    from app.models import Cuidador
    return Cuidador.query.get(int(user_id))