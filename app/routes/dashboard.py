from datetime import date, datetime
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import Idoso, Turno, Administracao

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    hoje = date.today()

    # todos os idosos cadastrados
    idosos = Idoso.query.filter_by().all()

    # turnos de hoje
    turnos_hoje = (
        Turno.query
        .filter(Turno.data == hoje)
        .order_by(Turno.periodo)
        .all()
    )

    # administrações pendentes hoje (para todos os idosos)
    pendentes = (
        Administracao.query
        .filter(
            Administracao.status == "pendente",
            Administracao.data_prevista >= datetime.combine(hoje, datetime.min.time()),
            Administracao.data_prevista <  datetime.combine(hoje, datetime.max.time()),
        )
        .order_by(Administracao.data_prevista)
        .all()
    )

    # turno ativo do cuidador logado hoje
    meu_turno = (
        Turno.query
        .filter(
            Turno.data == hoje,
            Turno.cuidador_id == current_user.id,
        )
        .first()
    )

    return render_template(
        "dashboard/index.html",
        idosos=idosos,
        turnos_hoje=turnos_hoje,
        pendentes=pendentes,
        meu_turno=meu_turno,
        hoje=hoje,
    )