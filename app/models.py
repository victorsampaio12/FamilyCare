from datetime import datetime, date, time
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


# ─────────────────────────────────────────────
#  CUIDADOR (filho / familiar)
# ─────────────────────────────────────────────
class Cuidador(UserMixin, db.Model):
    __tablename__ = "cuidadores"

    id            = db.Column(db.Integer, primary_key=True)
    nome          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    telefone      = db.Column(db.String(20))
    senha_hash    = db.Column(db.String(256), nullable=False)
    eh_admin      = db.Column(db.Boolean, default=False)   # quem pode editar tudo
    criado_em     = db.Column(db.DateTime, default=datetime.utcnow)

    # relacionamentos
    turnos        = db.relationship("Turno",           back_populates="cuidador", lazy="dynamic")
    registros     = db.relationship("RegistroCuidado", back_populates="cuidador", lazy="dynamic")
    administracoes = db.relationship("Administracao",  back_populates="cuidador", lazy="dynamic")

    def set_senha(self, senha: str):
        self.senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f"<Cuidador {self.nome}>"


# ─────────────────────────────────────────────
#  IDOSO
# ─────────────────────────────────────────────
class Idoso(db.Model):
    __tablename__ = "idosos"

    id               = db.Column(db.Integer, primary_key=True)
    nome             = db.Column(db.String(120), nullable=False)
    data_nascimento  = db.Column(db.Date,    nullable=False)
    condicoes        = db.Column(db.Text)    # diabetes, hipertensão, etc.
    observacoes      = db.Column(db.Text)    # alergias, preferências, etc.
    foto_url         = db.Column(db.String(300))
    criado_em        = db.Column(db.DateTime, default=datetime.utcnow)

    # relacionamentos
    medicamentos     = db.relationship("Medicamento",    back_populates="idoso", lazy="dynamic")
    turnos           = db.relationship("Turno",          back_populates="idoso",  lazy="dynamic")
    registros        = db.relationship("RegistroCuidado", back_populates="idoso", lazy="dynamic")

    @property
    def idade(self) -> int:
        hoje = date.today()
        return hoje.year - self.data_nascimento.year - (
            (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )

    def __repr__(self):
        return f"<Idoso {self.nome}>"


# ─────────────────────────────────────────────
#  MEDICAMENTO
# ─────────────────────────────────────────────
class Medicamento(db.Model):
    __tablename__ = "medicamentos"

    id            = db.Column(db.Integer, primary_key=True)
    idoso_id      = db.Column(db.Integer, db.ForeignKey("idosos.id"), nullable=False)
    nome          = db.Column(db.String(120), nullable=False)
    dosagem       = db.Column(db.String(60))    # ex: "500mg", "2 comprimidos"
    instrucoes    = db.Column(db.Text)           # ex: "tomar com água, após refeição"
    data_inicio   = db.Column(db.Date, nullable=False, default=date.today)
    data_fim      = db.Column(db.Date)           # None = uso contínuo
    ativo         = db.Column(db.Boolean, default=True)
    criado_em     = db.Column(db.DateTime, default=datetime.utcnow)

    # relacionamentos
    idoso         = db.relationship("Idoso",        back_populates="medicamentos")
    horarios      = db.relationship("HorarioRemedio", back_populates="medicamento",
                                    cascade="all, delete-orphan", lazy="dynamic")
    administracoes = db.relationship("Administracao", back_populates="medicamento", lazy="dynamic")

    def __repr__(self):
        return f"<Medicamento {self.nome} — {self.dosagem}>"


# ─────────────────────────────────────────────
#  HORÁRIO DO REMÉDIO  (1 medicamento → N horários por semana)
# ─────────────────────────────────────────────
DIAS_SEMANA = {0: "Seg", 1: "Ter", 2: "Qua", 3: "Qui", 4: "Sex", 5: "Sáb", 6: "Dom"}

class HorarioRemedio(db.Model):
    __tablename__ = "horarios_remedios"

    id             = db.Column(db.Integer, primary_key=True)
    medicamento_id = db.Column(db.Integer, db.ForeignKey("medicamentos.id"), nullable=False)
    # 0=Segunda … 6=Domingo; None = todos os dias
    dia_semana     = db.Column(db.SmallInteger)
    horario        = db.Column(db.Time, nullable=False)   # ex: time(8, 0)

    medicamento    = db.relationship("Medicamento", back_populates="horarios")

    def __repr__(self):
        dia = DIAS_SEMANA.get(self.dia_semana, "Diário")
        return f"<Horario {dia} {self.horario}>"


# ─────────────────────────────────────────────
#  ADMINISTRAÇÃO  (registro de que o remédio foi dado)
# ─────────────────────────────────────────────
class Administracao(db.Model):
    __tablename__ = "administracoes"

    id             = db.Column(db.Integer, primary_key=True)
    medicamento_id = db.Column(db.Integer, db.ForeignKey("medicamentos.id"), nullable=False)
    cuidador_id    = db.Column(db.Integer, db.ForeignKey("cuidadores.id"), nullable=False)
    # horário programado
    data_prevista  = db.Column(db.DateTime, nullable=False)
    # horário real em que foi administrado (None = ainda não foi)
    data_real      = db.Column(db.DateTime)
    status         = db.Column(
        db.Enum("pendente", "administrado", "pulado", name="status_adm"),
        default="pendente", nullable=False
    )
    observacao     = db.Column(db.Text)   # ex: "vomitou logo após"

    medicamento    = db.relationship("Medicamento", back_populates="administracoes")
    cuidador       = db.relationship("Cuidador",    back_populates="administracoes")

    def __repr__(self):
        return f"<Adm {self.medicamento_id} | {self.status} | {self.data_prevista}>"


# ─────────────────────────────────────────────
#  TURNO
# ─────────────────────────────────────────────
class Turno(db.Model):
    __tablename__ = "turnos"

    id           = db.Column(db.Integer, primary_key=True)
    idoso_id     = db.Column(db.Integer, db.ForeignKey("idosos.id"),     nullable=False)
    cuidador_id  = db.Column(db.Integer, db.ForeignKey("cuidadores.id"), nullable=False)
    data         = db.Column(db.Date,    nullable=False)
    periodo      = db.Column(
        db.Enum("manha", "tarde", "noite", name="periodo_turno"),
        nullable=False
    )
    # horários reais do turno (podem diferir do padrão)
    hora_inicio  = db.Column(db.Time)
    hora_fim     = db.Column(db.Time)
    status       = db.Column(
        db.Enum("agendado", "em_andamento", "concluido", "cancelado", name="status_turno"),
        default="agendado", nullable=False
    )
    observacao   = db.Column(db.Text)
    criado_em    = db.Column(db.DateTime, default=datetime.utcnow)

    # relacionamentos
    idoso        = db.relationship("Idoso",    back_populates="turnos")
    cuidador     = db.relationship("Cuidador", back_populates="turnos")
    registros    = db.relationship("RegistroCuidado", back_populates="turno",
                                   cascade="all, delete-orphan", lazy="dynamic")

    __table_args__ = (
        # evita dois turnos do mesmo período para o mesmo idoso no mesmo dia
        db.UniqueConstraint("idoso_id", "data", "periodo", name="uq_turno_idoso_dia_periodo"),
    )

    def __repr__(self):
        return f"<Turno {self.data} {self.periodo} — {self.cuidador_id}>"


# ─────────────────────────────────────────────
#  REGISTRO DE CUIDADO  (diário do turno)
# ─────────────────────────────────────────────
class RegistroCuidado(db.Model):
    __tablename__ = "registros_cuidado"

    id              = db.Column(db.Integer, primary_key=True)
    turno_id        = db.Column(db.Integer, db.ForeignKey("turnos.id"),      nullable=False)
    idoso_id        = db.Column(db.Integer, db.ForeignKey("idosos.id"),      nullable=False)
    cuidador_id     = db.Column(db.Integer, db.ForeignKey("cuidadores.id"),  nullable=False)
    criado_em       = db.Column(db.DateTime, default=datetime.utcnow)

    # campos de saúde e bem-estar
    humor           = db.Column(
        db.Enum("otimo", "bom", "neutro", "agitado", "triste", name="humor_idoso")
    )
    alimentacao     = db.Column(db.Text)   # o que comeu / recusou
    hidratacao      = db.Column(db.Text)   # quantidade de líquidos
    eliminacoes     = db.Column(db.Text)   # intestino, urina (privacidade clínica)
    mobilidade      = db.Column(db.Text)   # ficou deitado, sentou, andou
    intercorrencias = db.Column(db.Text)   # quedas, dor, febre, etc.
    observacoes     = db.Column(db.Text)   # notas livres

    # relacionamentos
    turno           = db.relationship("Turno",    back_populates="registros")
    idoso           = db.relationship("Idoso",    back_populates="registros")
    cuidador        = db.relationship("Cuidador", back_populates="registros")

    def __repr__(self):
        return f"<Registro turno={self.turno_id} cuidador={self.cuidador_id}>"