"""
Seed — popula o banco com dados iniciais para teste.

Uso:
    python seed.py

Isso cria:
  • 3 cuidadores (Maria, João e Ana) — senha: 123456
  • 1 idosa (Dona Helena, 82 anos)
  • 3 medicamentos com horários
  • Turnos para a semana atual (seg → dom)
"""

import os
from datetime import date, time, datetime, timedelta

# garante que o .env é carregado antes de importar a app
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import Cuidador, Idoso, Medicamento, HorarioRemedio, Turno

app = create_app("development")

PERIODOS = ["manha", "tarde", "noite"]

def semana_atual():
    """Retorna os 7 dias da semana corrente (seg → dom)."""
    hoje = date.today()
    seg  = hoje - timedelta(days=hoje.weekday())
    return [seg + timedelta(days=i) for i in range(7)]

def seed():
    with app.app_context():
        # ── limpa tudo (ordem importa por FK) ──────────────────
        Turno.query.delete()
        HorarioRemedio.query.delete()
        Medicamento.query.delete()
        Idoso.query.delete()
        Cuidador.query.delete()
        db.session.commit()

        print("🌱 Iniciando seed...")

        # ── cuidadores ─────────────────────────────────────────
        dados_cuidadores = [
            ("Maria Silva",  "maria@helpage.com",  "61999990001", True),
            ("João Silva",   "joao@helpage.com",   "61999990002", False),
            ("Ana Lima",     "ana@helpage.com",    "61999990003", False),
        ]
        cuidadores = []
        for nome, email, tel, admin in dados_cuidadores:
            c = Cuidador(nome=nome, email=email, telefone=tel, eh_admin=admin)
            c.set_senha("123456")
            db.session.add(c)
            cuidadores.append(c)

        db.session.flush()
        print(f"  ✓ {len(cuidadores)} cuidadores criados")

        # ── idoso ───────────────────────────────────────────────
        helena = Idoso(
            nome            = "Helena Rodrigues",
            data_nascimento = date(1943, 3, 12),
            condicoes       = "Hipertensão, Diabetes tipo 2, Osteoporose",
            observacoes     = "Alergia a Penicilina. Prefere banho pela manhã. "
                              "Gosta de ouvir rádio gospel. Dorme às 21h.",
        )
        db.session.add(helena)
        db.session.flush()
        print(f"  ✓ Idoso '{helena.nome}' criado")

        # ── medicamentos ────────────────────────────────────────
        meds_dados = [
            {
                "nome": "Losartana",
                "dosagem": "50mg",
                "instrucoes": "Tomar com água após o café da manhã.",
                "horarios": [(time(8, 0), None), (time(20, 0), None)],
            },
            {
                "nome": "Metformina",
                "dosagem": "850mg",
                "instrucoes": "Tomar imediatamente após o almoço. Não partir o comprimido.",
                "horarios": [(time(12, 0), None)],
            },
            {
                "nome": "Cálcio + Vitamina D",
                "dosagem": "600mg + 400UI",
                "instrucoes": "Tomar após o jantar.",
                "horarios": [(time(19, 0), None)],
            },
        ]

        for md in meds_dados:
            med = Medicamento(
                idoso_id    = helena.id,
                nome        = md["nome"],
                dosagem     = md["dosagem"],
                instrucoes  = md["instrucoes"],
                data_inicio = date.today(),
            )
            db.session.add(med)
            db.session.flush()
            for horario, dia in md["horarios"]:
                db.session.add(HorarioRemedio(
                    medicamento_id = med.id,
                    horario        = horario,
                    dia_semana     = dia,
                ))

        print(f"  ✓ {len(meds_dados)} medicamentos criados")

        # ── turnos da semana ────────────────────────────────────
        semana = semana_atual()
        hoje   = date.today()

        # rodízio: Maria=manhã, João=tarde, Ana=noite (rotacionando por dia)
        escalas = {
            "manha": [cuidadores[0], cuidadores[1], cuidadores[2],
                      cuidadores[0], cuidadores[1], cuidadores[2], cuidadores[0]],
            "tarde": [cuidadores[1], cuidadores[2], cuidadores[0],
                      cuidadores[1], cuidadores[2], cuidadores[0], cuidadores[1]],
            "noite": [cuidadores[2], cuidadores[0], cuidadores[1],
                      cuidadores[2], cuidadores[0], cuidadores[1], cuidadores[2]],
        }

        turnos_criados = 0
        for i, dia in enumerate(semana):
            for periodo in PERIODOS:
                cuidador = escalas[periodo][i]

                if dia < hoje:
                    status = "concluido"
                elif dia == hoje and periodo == "manha":
                    status = "em_andamento"
                else:
                    status = "agendado"

                turno = Turno(
                    idoso_id    = helena.id,
                    cuidador_id = cuidador.id,
                    data        = dia,
                    periodo     = periodo,
                    status      = status,
                )
                db.session.add(turno)
                turnos_criados += 1

        print(f"  ✓ {turnos_criados} turnos criados para a semana")

        db.session.commit()
        print("\n✅ Seed concluído com sucesso!")
        print("\nCredenciais de acesso:")
        print("  maria@helpage.com  /  123456  (admin)")
        print("  joao@helpage.com   /  123456")
        print("  ana@helpage.com    /  123456")


if __name__ == "__main__":
    seed()