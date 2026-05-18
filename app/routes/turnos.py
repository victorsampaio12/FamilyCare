from datetime import date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.models import Idoso, Cuidador, Turno

turnos_bp = Blueprint("turnos", __name__)

PERIODOS = ("manha", "tarde", "noite")


# ── escala semanal ────────────────────────────────────────────
@turnos_bp.route("/")
@login_required
def index():
    # semana atual (segunda → domingo)
    hoje  = date.today()
    seg   = hoje - timedelta(days=hoje.weekday())
    semana = [seg + timedelta(days=i) for i in range(7)]

    idosos   = Idoso.query.all()
    cuidadores = Cuidador.query.order_by(Cuidador.nome).all()

    turnos = (
        Turno.query
        .filter(Turno.data >= semana[0], Turno.data <= semana[-1])
        .all()
    )

    # índice para facilitar o template: {(idoso_id, data, periodo): turno}
    idx = {(t.idoso_id, t.data, t.periodo): t for t in turnos}

    return render_template(
        "turnos/index.html",
        semana=semana,
        idosos=idosos,
        cuidadores=cuidadores,
        periodos=PERIODOS,
        idx=idx,
        hoje=hoje,
    )


# ── agendar turno ─────────────────────────────────────────────
@turnos_bp.route("/agendar", methods=["POST"])
@login_required
def agendar():
    idoso_id    = request.form.get("idoso_id",    type=int)
    cuidador_id = request.form.get("cuidador_id", type=int)
    data_str    = request.form.get("data")
    periodo     = request.form.get("periodo")

    if not all([idoso_id, cuidador_id, data_str, periodo]):
        flash("Preencha todos os campos.", "danger")
        return redirect(url_for("turnos.index"))

    data = date.fromisoformat(data_str)

    # verifica conflito (UniqueConstraint no model)
    existente = Turno.query.filter_by(idoso_id=idoso_id, data=data, periodo=periodo).first()
    if existente:
        flash("Já existe um turno agendado para esse período.", "warning")
        return redirect(url_for("turnos.index"))

    turno = Turno(
        idoso_id    = idoso_id,
        cuidador_id = cuidador_id,
        data        = data,
        periodo     = periodo,
    )
    db.session.add(turno)
    db.session.commit()
    flash("Turno agendado.", "success")
    return redirect(url_for("turnos.index"))


# ── trocar responsável do turno ───────────────────────────────
@turnos_bp.route("/<int:turno_id>/trocar", methods=["POST"])
@login_required
def trocar(turno_id):
    turno = Turno.query.get_or_404(turno_id)
    novo_cuidador_id = request.form.get("cuidador_id", type=int)

    if not novo_cuidador_id:
        flash("Selecione um cuidador.", "danger")
        return redirect(url_for("turnos.index"))

    turno.cuidador_id = novo_cuidador_id
    db.session.commit()
    flash("Responsável do turno atualizado.", "success")
    return redirect(url_for("turnos.index"))


# ── atualizar status do turno ─────────────────────────────────
@turnos_bp.route("/<int:turno_id>/status", methods=["POST"])
@login_required
def atualizar_status(turno_id):
    turno  = Turno.query.get_or_404(turno_id)
    status = request.form.get("status")

    if status not in ("agendado", "em_andamento", "concluido", "cancelado"):
        flash("Status inválido.", "danger")
        return redirect(url_for("turnos.index"))

    turno.status = status
    db.session.commit()
    flash("Status do turno atualizado.", "success")
    return redirect(request.referrer or url_for("turnos.index"))


# ── cancelar turno ────────────────────────────────────────────
@turnos_bp.route("/<int:turno_id>/cancelar", methods=["POST"])
@login_required
def cancelar(turno_id):
    turno = Turno.query.get_or_404(turno_id)
    turno.status = "cancelado"
    db.session.commit()
    flash("Turno cancelado.", "info")
    return redirect(url_for("turnos.index"))