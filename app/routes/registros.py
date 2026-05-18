from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.models import Turno, RegistroCuidado

registros_bp = Blueprint("registros", __name__)

HUMORES = ["otimo", "bom", "neutro", "agitado", "triste"]


# ── histórico geral ───────────────────────────────────────────
@registros_bp.route("/")
@login_required
def index():
    registros = (
        RegistroCuidado.query
        .order_by(RegistroCuidado.criado_em.desc())
        .limit(50)
        .all()
    )
    return render_template("registros/index.html", registros=registros)


# ── novo registro (vinculado a um turno) ──────────────────────
@registros_bp.route("/novo/<int:turno_id>", methods=["GET", "POST"])
@login_required
def novo(turno_id):
    turno = Turno.query.get_or_404(turno_id)

    # impede registro duplicado no mesmo turno pelo mesmo cuidador
    existente = RegistroCuidado.query.filter_by(
        turno_id=turno_id, cuidador_id=current_user.id
    ).first()

    if existente:
        flash("Você já registrou este turno. Use editar.", "warning")
        return redirect(url_for("registros.editar", reg_id=existente.id))

    if request.method == "POST":
        reg = RegistroCuidado(
            turno_id        = turno_id,
            idoso_id        = turno.idoso_id,
            cuidador_id     = current_user.id,
            humor           = request.form.get("humor") or None,
            alimentacao     = request.form.get("alimentacao", "").strip() or None,
            hidratacao      = request.form.get("hidratacao", "").strip() or None,
            eliminacoes     = request.form.get("eliminacoes", "").strip() or None,
            mobilidade      = request.form.get("mobilidade", "").strip() or None,
            intercorrencias = request.form.get("intercorrencias", "").strip() or None,
            observacoes     = request.form.get("observacoes", "").strip() or None,
        )
        db.session.add(reg)

        # marca turno como concluído
        turno.status = "concluido"
        db.session.commit()

        flash("Registro do turno salvo.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("registros/form.html", turno=turno, humores=HUMORES)


# ── editar registro ───────────────────────────────────────────
@registros_bp.route("/<int:reg_id>/editar", methods=["GET", "POST"])
@login_required
def editar(reg_id):
    reg = RegistroCuidado.query.get_or_404(reg_id)

    if request.method == "POST":
        reg.humor           = request.form.get("humor") or None
        reg.alimentacao     = request.form.get("alimentacao", "").strip() or None
        reg.hidratacao      = request.form.get("hidratacao", "").strip() or None
        reg.eliminacoes     = request.form.get("eliminacoes", "").strip() or None
        reg.mobilidade      = request.form.get("mobilidade", "").strip() or None
        reg.intercorrencias = request.form.get("intercorrencias", "").strip() or None
        reg.observacoes     = request.form.get("observacoes", "").strip() or None
        db.session.commit()

        flash("Registro atualizado.", "success")
        return redirect(url_for("registros.index"))

    return render_template("registros/form.html", reg=reg, turno=reg.turno, humores=HUMORES)


# ── detalhe de um registro ────────────────────────────────────
@registros_bp.route("/<int:reg_id>")
@login_required
def detalhe(reg_id):
    reg = RegistroCuidado.query.get_or_404(reg_id)
    return render_template("registros/detalhe.html", reg=reg)