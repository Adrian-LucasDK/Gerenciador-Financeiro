import os
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect, FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField, SelectField, DecimalField, DateField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-chave-trocar-antes-de-publicar")
# Banco SQLite armazenado localmente na pasta instance/.
# O sistema foi preparado para uso somente na rede local.
instance_dir = Path(app.instance_path)
instance_dir.mkdir(parents=True, exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(instance_dir / "financeiro.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Entre na sua conta para continuar."
login_manager.login_message_category = "warning"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    transactions = db.relationship("Transaction", backref="owner", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    description = db.Column(db.String(140), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    kind = db.Column(db.String(10), nullable=False)  # income / expense
    category = db.Column(db.String(50), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False, default=date.today)
    notes = db.Column(db.String(500))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

class RegisterForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=160)])
    password = PasswordField("Senha", validators=[DataRequired(), Length(min=8, message="Use pelo menos 8 caracteres.")])
    confirm = PasswordField("Confirmar senha", validators=[DataRequired(), EqualTo("password", message="As senhas não conferem.")])
    submit = SubmitField("Criar conta")

class LoginForm(FlaskForm):
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    password = PasswordField("Senha", validators=[DataRequired()])
    submit = SubmitField("Entrar")

class AdminUserForm(FlaskForm):
    name = StringField(
        "Nome",
        validators=[DataRequired(), Length(min=2, max=80)]
    )

    email = StringField(
        "E-mail",
        validators=[DataRequired(), Email(), Length(max=160)]
    )

    password = PasswordField(
        "Senha",
        validators=[
            DataRequired(),
            Length(min=8, message="A senha deve ter pelo menos 8 caracteres.")
        ]
    )

    role = SelectField(
        "Tipo de usuário",
        choices=[
            ("user", "Usuário comum"),
            ("admin", "Administrador")
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField("Criar usuário")

class TransactionForm(FlaskForm):
    description = StringField("Descrição", validators=[DataRequired(), Length(max=140)])
    amount = DecimalField("Valor (R$)", places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    kind = SelectField("Tipo", choices=[("expense", "Despesa"), ("income", "Receita")], validators=[DataRequired()])
    category = SelectField("Categoria", choices=[
        ("Alimentação", "Alimentação"), ("Moradia", "Moradia"), ("Transporte", "Transporte"),
        ("Saúde", "Saúde"), ("Educação", "Educação"), ("Lazer", "Lazer"),
        ("Salário", "Salário"), ("Serviços", "Serviços"), ("Compras", "Compras"), ("Outros", "Outros")
    ], validators=[DataRequired()])
    transaction_date = DateField("Data", validators=[DataRequired()], default=date.today)
    notes = TextAreaField("Observações", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Salvar lançamento")

def create_admin_from_env():
    email = os.getenv(
        "ADMIN_EMAIL",
        "admin@financeiro.com.br"
    )

    password = os.getenv(
        "ADMIN_PASSWORD",
        "Financeiro@2026"
    )

    # Corrige o e-mail antigo, caso já tenha sido cadastrado.
    antigo = User.query.filter_by(
        email="admin@financeiro.local"
    ).first()

    if antigo:
        antigo.email = email.lower().strip()
        db.session.commit()

    # Cria o administrador se ainda não existir.
    if not User.query.filter_by(role="admin").first():
        admin = User(
            name="Administrador",
            email=email.lower().strip(),
            role="admin"
        )

        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/registrar", methods=["GET", "POST"])
def register():
    if os.getenv("ALLOW_REGISTRATION", "1") != "1":
        flash("O cadastro público está desativado.", "warning")
        return redirect(url_for("login"))
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        if User.query.filter_by(email=email).first():
            flash("Este e-mail já está cadastrado.", "danger")
        else:
            user = User(name=form.name.data.strip(), email=email)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Conta criada com sucesso!", "success")
            return redirect(url_for("dashboard"))
    return render_template("register.html", form=form)

@app.route("/entrar", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("E-mail ou senha inválidos.", "danger")
    return render_template("login.html", form=form)

@app.post("/sair")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("login"))

@app.route("/painel")
@login_required
def dashboard():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(
        Transaction.transaction_date.desc(), Transaction.id.desc()).limit(8).all()
    income = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).filter_by(
        user_id=current_user.id, kind="income").scalar()
    expenses = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).filter_by(
        user_id=current_user.id, kind="expense").scalar()
    return render_template("dashboard.html", transactions=transactions,
                           income=Decimal(income), expenses=Decimal(expenses),
                           balance=Decimal(income)-Decimal(expenses))

@app.route("/lancamentos")
@login_required
def transactions():
    items = Transaction.query.filter_by(user_id=current_user.id).order_by(
        Transaction.transaction_date.desc(), Transaction.id.desc()).all()
    return render_template("transactions.html", transactions=items)

@app.route("/lancamentos/novo", methods=["GET", "POST"])
@login_required
def transaction_new():
    form = TransactionForm()
    if form.validate_on_submit():
        item = Transaction(user_id=current_user.id, description=form.description.data.strip(),
                           amount=form.amount.data, kind=form.kind.data, category=form.category.data,
                           transaction_date=form.transaction_date.data, notes=form.notes.data)
        db.session.add(item)
        db.session.commit()
        flash("Lançamento adicionado.", "success")
        return redirect(url_for("transactions"))
    return render_template("transaction_form.html", form=form, heading="Novo lançamento")

@app.route("/lancamentos/<int:item_id>/editar", methods=["GET", "POST"])
@login_required
def transaction_edit(item_id):
    item = Transaction.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    form = TransactionForm(obj=item)
    if form.validate_on_submit():
        item.description = form.description.data.strip()
        item.amount = form.amount.data
        item.kind = form.kind.data
        item.category = form.category.data
        item.transaction_date = form.transaction_date.data
        item.notes = form.notes.data
        db.session.commit()
        flash("Lançamento atualizado.", "success")
        return redirect(url_for("transactions"))
    return render_template("transaction_form.html", form=form, heading="Editar lançamento")

@app.post("/lancamentos/<int:item_id>/excluir")
@login_required
def transaction_delete(item_id):
    item = Transaction.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Lançamento excluído.", "info")
    return redirect(url_for("transactions"))

@app.route("/admin/usuarios")
@login_required
def users_admin():
    if current_user.role != "admin":
        abort(403)
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("users.html", users=users)

@app.route("/admin/usuarios/novo", methods=["GET", "POST"])
@login_required
def user_create():
    # Somente administradores podem criar usuários.
    if current_user.role != "admin":
        abort(403)

    form = AdminUserForm()

    if form.validate_on_submit():
        email = form.email.data.lower().strip()

        # Verifica se o e-mail já está cadastrado.
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Este e-mail já está cadastrado.", "danger")
            return render_template("user_form.html", form=form)

        # Cria o novo usuário.
        user = User(
            name=form.name.data.strip(),
            email=email,
            role=form.role.data
        )

        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Usuário criado com sucesso!", "success")
        return redirect(url_for("users_admin"))

    return render_template("user_form.html", form=form)

@app.post("/admin/usuarios/<int:user_id>/excluir")
@login_required
def user_delete(user_id):
    if current_user.role != "admin":
        abort(403)
    if user_id == current_user.id:
        flash("Por segurança, o administrador não pode excluir a própria conta.", "danger")
        return redirect(url_for("users_admin"))
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.role == "admin" and User.query.filter_by(role="admin").count() <= 1:
        flash("Não é possível excluir o último administrador.", "danger")
        return redirect(url_for("users_admin"))
    db.session.delete(user)  # os lançamentos do usuário também são removidos
    db.session.commit()
    flash(f"Usuário {user.email} e todos os seus lançamentos foram excluídos.", "info")
    return redirect(url_for("users_admin"))

@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, message="Você não tem permissão para acessar esta página."), 403

@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="O conteúdo solicitado não foi encontrado."), 404

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_admin_from_env()

    app.run(host="0.0.0.0", port=5000, debug=False)
