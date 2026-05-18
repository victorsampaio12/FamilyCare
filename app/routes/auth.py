from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models import Cuidador

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        cuidador = Cuidador.query.filter_by(email=email).first()

        if cuidador and cuidador.checar_senha(senha):
            login_user(cuidador, remember=request.form.get("lembrar") == "on")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))

        flash("E-mail ou senha incorretos.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sessão.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        nome     = request.form.get("nome", "").strip()
        email    = request.form.get("email", "").strip().lower()
        telefone = request.form.get("telefone", "").strip()
        senha    = request.form.get("senha", "")
        confirma = request.form.get("confirma_senha", "")

        erro = None
        if not nome or not email or not senha:
            erro = "Preencha todos os campos obrigatórios."
        elif senha != confirma:
            erro = "As senhas não coincidem."
        elif Cuidador.query.filter_by(email=email).first():
            erro = "Este e-mail já está cadastrado."

        if erro:
            flash(erro, "danger")
        else:
            cuidador = Cuidador(nome=nome, email=email, telefone=telefone)
            cuidador.set_senha(senha)
            db.session.add(cuidador)
            db.session.commit()
            flash("Cadastro realizado! Faça login.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/cadastro.html")