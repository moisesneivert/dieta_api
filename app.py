from flask import Flask, request, jsonify
from models.user import User
from models.meal import Meal
from database import db
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
import bcrypt
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:admin123@127.0.0.1:3306/flask-crud'

login_manager = LoginManager()
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


#### ===================== AUTENTICAÇÃO ===================== ####

@app.route('/login', methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username and password:
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.checkpw(str.encode(password), str.encode(user.password)):
            login_user(user)
            return jsonify({"message": "Autenticação realizada com sucesso"})

    return jsonify({"message": "Credenciais inválidas"}), 400


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout realizado com sucesso!"})


#### ===================== CRUD DE USUÁRIOS ===================== ####

@app.route('/user', methods=["POST"])
def create_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username and password:
        hashed_password = bcrypt.hashpw(str.encode(password), bcrypt.gensalt())
        user = User(username=username, password=hashed_password, role='user')
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "Usuario cadastrado com sucesso"})

    return jsonify({"message": "Dados invalidos"}), 400


@app.route('/user/<int:id_user>', methods=["GET"])
@login_required
def read_user(id_user):
    user = User.query.get(id_user)

    if user:
        return {"username": user.username}

    return jsonify({"message": "Usuario não encontrado"}), 404


@app.route('/user/<int:id_user>', methods=["PUT"])
@login_required
def update_user(id_user):
    data = request.json
    user = User.query.get(id_user)

    if id_user != current_user.id and current_user.role == "user":
        return jsonify({"message": "Operação não permitida"}), 403

    if user and data.get("password"):
        user.password = data.get("password")
        db.session.commit()

        return jsonify({"message": f"Usuário {id_user} atualizado com sucesso"})
    
    return jsonify({"message": "Usuario não encontrado"}), 404


@app.route('/user/<int:id_user>', methods=["DELETE"])
@login_required
def delete_user(id_user):
    user = User.query.get(id_user)
    
    if current_user.role != 'admin':
        return jsonify({"message": "Operação não permitida"}), 403

    if id_user == current_user.id:
        return jsonify({"message": "Deleção não permitida"}), 403

    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": f"Usuário {id_user} deletado com sucesso"})
    
    return jsonify({"message": "Usuario não encontrado"}), 404


#### ===================== CRUD DE REFEIÇÕES (DIETA) ===================== ####

def parse_datetime(datetime_str):
    """
    Espera string em formato ISO 8601, por exemplo:
    "2025-11-15T12:30:00"
    """
    try:
        return datetime.fromisoformat(datetime_str)
    except Exception:
        return None


@app.route('/meals', methods=["POST"])
@login_required
def create_meal():
    """
    Registro de refeição:
    {
        "name": "Almoço",
        "description": "Arroz, feijão e frango grelhado",
        "datetime": "2025-11-15T12:30:00",
        "in_diet": true
    }
    """
    data = request.json or {}

    name = data.get("name")
    description = data.get("description")
    datetime_str = data.get("datetime")
    in_diet = data.get("in_diet")

    if not name or not datetime_str or in_diet is None:
        return jsonify({"message": "Campos obrigatórios: name, datetime, in_diet"}), 400

    meal_datetime = parse_datetime(datetime_str)
    if not meal_datetime:
        return jsonify({"message": "Formato de data e hora inválido, use ISO 8601, exemplo: 2025-11-15T12:30:00"}), 400

    meal = Meal(
        name=name,
        description=description,
        datetime=meal_datetime,
        in_diet=bool(in_diet),
        user_id=current_user.id
    )

    db.session.add(meal)
    db.session.commit()

    return jsonify({"message": "Refeição registrada com sucesso", "meal": meal.to_dict()}), 201


@app.route('/meals', methods=["GET"])
@login_required
def list_meals():
    """
    Lista todas as refeições do usuário logado.
    """
    meals = Meal.query.filter_by(user_id=current_user.id).order_by(Meal.datetime.desc()).all()
    return jsonify([meal.to_dict() for meal in meals])


@app.route('/meals/<int:meal_id>', methods=["GET"])
@login_required
def get_meal(meal_id):
    """
    Visualização de uma única refeição.
    """
    meal = Meal.query.filter_by(id=meal_id, user_id=current_user.id).first()

    if not meal:
        return jsonify({"message": "Refeição não encontrada"}), 404

    return jsonify(meal.to_dict())


@app.route('/meals/<int:meal_id>', methods=["PUT"])
@login_required
def update_meal(meal_id):
    """
    Edita uma refeição alterando todos os dados.
    Espera o mesmo formato do POST.
    """
    data = request.json or {}

    meal = Meal.query.filter_by(id=meal_id, user_id=current_user.id).first()
    if not meal:
        return jsonify({"message": "Refeição não encontrada"}), 404

    name = data.get("name")
    description = data.get("description")
    datetime_str = data.get("datetime")
    in_diet = data.get("in_diet")

    if not name or not datetime_str or in_diet is None:
        return jsonify({"message": "Campos obrigatórios: name, datetime, in_diet"}), 400

    meal_datetime = parse_datetime(datetime_str)
    if not meal_datetime:
        return jsonify({"message": "Formato de data e hora inválido, use ISO 8601, exemplo: 2025-11-15T12:30:00"}), 400

    meal.name = name
    meal.description = description
    meal.datetime = meal_datetime
    meal.in_diet = bool(in_diet)

    db.session.commit()

    return jsonify({"message": "Refeição atualizada com sucesso", "meal": meal.to_dict()})


@app.route('/meals/<int:meal_id>', methods=["DELETE"])
@login_required
def delete_meal(meal_id):
    """
    Deleta uma refeição do usuário logado.
    """
    meal = Meal.query.filter_by(id=meal_id, user_id=current_user.id).first()

    if not meal:
        return jsonify({"message": "Refeição não encontrada"}), 404

    db.session.delete(meal)
    db.session.commit()

    return jsonify({"message": "Refeição deletada com sucesso"}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
