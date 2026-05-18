from datetime import date, datetime, time
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.models import Idoso, Medicamento, HorarioRemedio, Administracao

medicamentos_bp = Blueprint("medicamentos", __name__)


# ── listagem ──────────────────────────────────────────────────
@medicamentos_bp.route("/")
@login_required
def index():
    idosos = Idoso.query.all()
    return render_template("medicamentos/index.html", idosos=idosos)


# ── novo medicamento ──────────────────────────────────────────
@medicamentos_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    idosos = Idoso.query.all()

    if request.method == "POST":
        idoso_id    = request.form.get("idoso_id", type=int)
        nome        = request.form.get("nome", "").strip()
        dosagem     = request.form.get("dosagem", "").strip()
        instrucoes  = request.form.get("instrucoes", "").strip()
        data_inicio = request.form.get("data_inicio")
        data_fim    = request.form.get("data_fim") or None

        if not idoso_id or not nome or not data_inicio:
            flash("Preencha os campos obrigatórios.", "danger")
            return render_template("medicamentos/form.html", idosos=idosos, hoje=date.today())

        med = Medicamento(
            idoso_id    = idoso_id,
            nome        = nome,
            dosagem     = dosagem,
            instrucoes  = instrucoes,
            data_inicio = date.fromisoformat(data_inicio),
            data_fim    = date.fromisoformat(data_fim) if data_fim else None,
        )
        db.session.add(med)
        db.session.flush()

        horarios = request.form.getlist("horarios[]")
        dias     = request.form.getlist("dias[]")
        for h, d in zip(horarios, dias):
            if not h:
                continue
            hora = time.fromisoformat(h)
            dia  = int(d) if d and d != "todos" else None
            db.session.add(HorarioRemedio(medicamento_id=med.id, horario=hora, dia_semana=dia))

        db.session.commit()
        flash(f"Medicamento '{nome}' cadastrado.", "success")
        return redirect(url_for("medicamentos.index"))

    return render_template("medicamentos/form.html", idosos=idosos, hoje=date.today())


@medicamentos_bp.route("/<int:med_id>/editar", methods=["GET", "POST"])
@login_required
def editar(med_id):
    med    = Medicamento.query.get_or_404(med_id)
    idosos = Idoso.query.all()

    if request.method == "POST":
        med.nome       = request.form.get("nome", "").strip()
        med.dosagem    = request.form.get("dosagem", "").strip()
        med.instrucoes = request.form.get("instrucoes", "").strip()
        data_fim       = request.form.get("data_fim") or None
        med.data_fim   = date.fromisoformat(data_fim) if data_fim else None
        med.ativo      = request.form.get("ativo") == "on"

        for h in med.horarios:
            db.session.delete(h)

        horarios = request.form.getlist("horarios[]")
        dias     = request.form.getlist("dias[]")
        for h, d in zip(horarios, dias):
            if not h:
                continue
            hora = time.fromisoformat(h)
            dia  = int(d) if d and d != "todos" else None
            db.session.add(HorarioRemedio(medicamento_id=med.id, horario=hora, dia_semana=dia))

        db.session.commit()
        flash("Medicamento atualizado.", "success")
        return redirect(url_for("medicamentos.index"))

    return render_template("medicamentos/form.html", med=med, idosos=idosos, hoje=date.today())


# ── desativar medicamento ─────────────────────────────────────
@medicamentos_bp.route("/<int:med_id>/desativar", methods=["POST"])
@login_required
def desativar(med_id):
    med = Medicamento.query.get_or_404(med_id)
    med.ativo = False
    db.session.commit()
    flash(f"Medicamento '{med.nome}' desativado.", "info")
    return redirect(url_for("medicamentos.index"))


# ── marcar administração ──────────────────────────────────────
@medicamentos_bp.route("/administracao/<int:adm_id>", methods=["POST"])
@login_required
def registrar_administracao(adm_id):
    adm = Administracao.query.get_or_404(adm_id)
    status     = request.form.get("status")           # administrado | pulado
    observacao = request.form.get("observacao", "").strip()

    if status not in ("administrado", "pulado"):
        flash("Status inválido.", "danger")
        return redirect(url_for("dashboard.index"))

    adm.status      = status
    adm.data_real   = datetime.utcnow()
    adm.cuidador_id = current_user.id
    adm.observacao  = observacao
    db.session.commit()

    flash("Administração registrada.", "success")
    return redirect(request.referrer or url_for("dashboard.index"))