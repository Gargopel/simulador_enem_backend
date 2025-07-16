from flask import Blueprint, request, jsonify
from src.models.user import db, User
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# Chave secreta para JWT (em produção, usar variável de ambiente)
JWT_SECRET = 'sua_chave_secreta_jwt_aqui'

def token_required(f):
    """Decorator para verificar token JWT"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token é obrigatório'}), 401
        
        try:
            # Remover 'Bearer ' do token se presente
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        
        return f(current_user_id, *args, **kwargs)
    
    return decorated

@auth_bp.route('/registrar', methods=['POST'])
def registrar():
    """Registra um novo usuário"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Username, email e password são obrigatórios'}), 400
    
    username = data['username']
    email = data['email']
    password = data['password']
    
    # Verificar se o usuário já existe
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username já existe'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email já está em uso'}), 400
    
    # Validações básicas
    if len(username) < 3:
        return jsonify({'error': 'Username deve ter pelo menos 3 caracteres'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password deve ter pelo menos 6 caracteres'}), 400
    
    if '@' not in email:
        return jsonify({'error': 'Email inválido'}), 400
    
    # Criar novo usuário
    password_hash = generate_password_hash(password)
    novo_usuario = User(username=username, email=email, password_hash=password_hash)
    
    db.session.add(novo_usuario)
    db.session.commit()
    
    # Gerar token JWT
    token = jwt.encode({
        'user_id': novo_usuario.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }, JWT_SECRET, algorithm='HS256')
    
    return jsonify({
        'message': 'Usuário registrado com sucesso',
        'user': novo_usuario.to_dict(),
        'token': token
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Faz login do usuário"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username e password são obrigatórios'}), 400
    
    username = data['username']
    password = data['password']
    
    # Buscar usuário
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    # Gerar token JWT
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }, JWT_SECRET, algorithm='HS256')
    
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': token
    })

@auth_bp.route('/perfil', methods=['GET'])
@token_required
def get_perfil(current_user_id):
    """Retorna o perfil do usuário autenticado"""
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    return jsonify({
        'user': user.to_dict()
    })

@auth_bp.route('/atualizar-perfil', methods=['PUT'])
@token_required
def atualizar_perfil(current_user_id):
    """Atualiza o perfil do usuário autenticado"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados são obrigatórios'}), 400
    
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Atualizar campos permitidos
    if 'email' in data:
        email = data['email']
        if '@' not in email:
            return jsonify({'error': 'Email inválido'}), 400
        
        # Verificar se email já está em uso por outro usuário
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != current_user_id:
            return jsonify({'error': 'Email já está em uso'}), 400
        
        user.email = email
    
    if 'username' in data:
        username = data['username']
        if len(username) < 3:
            return jsonify({'error': 'Username deve ter pelo menos 3 caracteres'}), 400
        
        # Verificar se username já está em uso por outro usuário
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != current_user_id:
            return jsonify({'error': 'Username já existe'}), 400
        
        user.username = username
    
    db.session.commit()
    
    return jsonify({
        'message': 'Perfil atualizado com sucesso',
        'user': user.to_dict()
    })

@auth_bp.route('/alterar-senha', methods=['PUT'])
@token_required
def alterar_senha(current_user_id):
    """Altera a senha do usuário autenticado"""
    data = request.get_json()
    
    if not data or 'current_password' not in data or 'new_password' not in data:
        return jsonify({'error': 'Senha atual e nova senha são obrigatórias'}), 400
    
    current_password = data['current_password']
    new_password = data['new_password']
    
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Verificar senha atual
    if not check_password_hash(user.password_hash, current_password):
        return jsonify({'error': 'Senha atual incorreta'}), 400
    
    # Validar nova senha
    if len(new_password) < 6:
        return jsonify({'error': 'Nova senha deve ter pelo menos 6 caracteres'}), 400
    
    # Atualizar senha
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    return jsonify({
        'message': 'Senha alterada com sucesso'
    })

@auth_bp.route('/verificar-token', methods=['GET'])
@token_required
def verificar_token(current_user_id):
    """Verifica se o token é válido"""
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    return jsonify({
        'message': 'Token válido',
        'user': user.to_dict()
    })

