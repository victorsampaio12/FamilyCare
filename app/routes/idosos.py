from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

from app import db
from app.models import Idoso

idosos_bp = Blueprint("idosos", __name__, url_prefix="/idosos")


@idosos_bp.route("/")
@login_required
def index():
    idosos = Idoso.query.order_by(Idoso.nome).all()
    return render_template("idosos/index.html", idosos=idosos)


@idosos_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    if request.method == "POST":
        nome            = request.form.get("nome", "").strip()
        data_nascimento = request.form.get("data_nascimento")
        condicoes       = request.form.get("condicoes", "").strip()
        observacoes     = request.form.get("observacoes", "").strip()

        if not nome or not data_nascimento:
            flash("Nome e data de nascimento são obrigatórios.", "danger")
            return render_template("idosos/form.html")

        idoso = Idoso(
            nome            = nome,
            data_nascimento = date.fromisoformat(data_nascimento),
            condicoes       = condicoes or None,
            observacoes     = observacoes or None,
        )
        db.session.add(idoso)
        db.session.commit()
        flash(f"Idoso '{nome}' cadastrado com sucesso.", "success")
        return redirect(url_for("idosos.index"))

    return render_template("idosos/form.html")


@idosos_bp.route("/<int:idoso_id>/editar", methods=["GET", "POST"])
@login_required
def editar(idoso_id):
    idoso = Idoso.query.get_or_404(idoso_id)

    if request.method == "POST":
        idoso.nome            = request.form.get("nome", "").strip()
        data_nascimento       = request.form.get("data_nascimento")
        idoso.data_nascimento = date.fromisoformat(data_nascimento)
        idoso.condicoes       = request.form.get("condicoes", "").strip() or None
        idoso.observacoes     = request.form.get("observacoes", "").strip() or None

        db.session.commit()
        flash("Dados atualizados.", "success")
        return redirect(url_for("idosos.index"))

    return render_template("idosos/form.html", idoso=idoso)


@idosos_bp.route("/<int:idoso_id>/excluir", methods=["POST"])
@login_required
def excluir(idoso_id):
    idoso = Idoso.query.get_or_404(idoso_id)
    db.session.delete(idoso)
    db.session.commit()
    flash(f"Idoso '{idoso.nome}' removido.", "info")
    return redirect(url_for("idosos.index"))