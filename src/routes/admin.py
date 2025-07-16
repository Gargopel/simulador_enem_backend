from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.admin import Admin
from src.models.questao import Questao
from src.models.simulado import Simulado, RespostaSimulado, ResultadoSimulado
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from sqlalchemy import func, desc

admin_bp = Blueprint('admin', __name__)

# Chave secreta para JWT (em produção, usar variável de ambiente)
JWT_SECRET = 'sua_chave_secreta_admin_jwt_aqui'

def admin_token_required(f):
    """Decorator para verificar token JWT de administrador"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token é obrigatório'}), 401
        
        try:
            # Remove 'Bearer ' do token se presente
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            current_admin_id = data['admin_id']
            
            # Verificar se o admin existe e está ativo
            admin = Admin.query.get(current_admin_id)
            if not admin or not admin.ativo:
                return jsonify({'error': 'Administrador não encontrado ou inativo'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        
        return f(current_admin_id, *args, **kwargs)
    
    return decorated

@admin_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """Login de administrador"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username e password são obrigatórios'}), 400
    
    username = data['username']
    password = data['password']
    
    # Buscar administrador
    admin = Admin.query.filter_by(username=username).first()
    
    if not admin or not admin.check_password(password):
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    if not admin.ativo:
        return jsonify({'error': 'Conta de administrador desativada'}), 401
    
    # Atualizar último login
    admin.ultimo_login = datetime.datetime.utcnow()
    db.session.commit()
    
    # Gerar token JWT
    token = jwt.encode({
        'admin_id': admin.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, JWT_SECRET, algorithm='HS256')
    
    return jsonify({
        'message': 'Login realizado com sucesso',
        'token': token,
        'admin': admin.to_dict()
    })

@admin_bp.route('/admin/dashboard/stats', methods=['GET'])
@admin_token_required
def get_dashboard_stats(current_admin_id):
    """Retorna estatísticas gerais do sistema"""
    try:
        # Estatísticas básicas
        total_usuarios = User.query.count()
        total_questoes = Questao.query.count()
        total_simulados = Simulado.query.count()
        total_simulados_finalizados = Simulado.query.filter_by(finalizado=True).count()
        
        # Usuários ativos (que fizeram pelo menos um simulado)
        usuarios_ativos = db.session.query(User.id).join(Simulado).distinct().count()
        
        # Média de questões por simulado (usando contagem de respostas)
        media_questoes_simulado = db.session.query(func.avg(
            db.session.query(func.count(RespostaSimulado.id))
            .filter(RespostaSimulado.simulado_id == Simulado.id)
            .scalar_subquery()
        )).scalar() or 0
        
        # Estatísticas por área de conhecimento
        stats_por_area = db.session.query(
            Questao.area_conhecimento,
            func.count(Questao.id).label('total_questoes')
        ).group_by(Questao.area_conhecimento).all()
        
        # Simulados por mês (últimos 6 meses)
        simulados_por_mes = db.session.query(
            func.strftime('%Y-%m', Simulado.data_criacao).label('mes'),
            func.count(Simulado.id).label('total')
        ).filter(
            Simulado.data_criacao >= datetime.datetime.utcnow() - datetime.timedelta(days=180)
        ).group_by(func.strftime('%Y-%m', Simulado.data_criacao)).all()
        
        # Top 5 usuários mais ativos
        top_usuarios = db.session.query(
            User.username,
            func.count(Simulado.id).label('total_simulados')
        ).join(Simulado).group_by(User.id).order_by(desc('total_simulados')).limit(5).all()
        
        # Distribuição de notas (últimos simulados finalizados) - versão simplificada
        try:
            distribuicao_notas = []
            total_resultados = ResultadoSimulado.query.count()
            if total_resultados > 0:
                baixa = ResultadoSimulado.query.filter(ResultadoSimulado.nota_geral < 400).count()
                media = ResultadoSimulado.query.filter(
                    ResultadoSimulado.nota_geral >= 400, 
                    ResultadoSimulado.nota_geral < 600
                ).count()
                boa = ResultadoSimulado.query.filter(
                    ResultadoSimulado.nota_geral >= 600, 
                    ResultadoSimulado.nota_geral < 800
                ).count()
                excelente = ResultadoSimulado.query.filter(ResultadoSimulado.nota_geral >= 800).count()
                
                distribuicao_notas = [
                    {'faixa': 'Baixa (0-399)', 'quantidade': baixa},
                    {'faixa': 'Média (400-599)', 'quantidade': media},
                    {'faixa': 'Boa (600-799)', 'quantidade': boa},
                    {'faixa': 'Excelente (800-1000)', 'quantidade': excelente}
                ]
        except Exception as e:
            distribuicao_notas = []
        
        return jsonify({
            'estatisticas_gerais': {
                'total_usuarios': total_usuarios,
                'total_questoes': total_questoes,
                'total_simulados': total_simulados,
                'total_simulados_finalizados': total_simulados_finalizados,
                'usuarios_ativos': usuarios_ativos,
                'media_questoes_simulado': round(media_questoes_simulado, 1)
            },
            'questoes_por_area': [
                {'area': area, 'total': total} 
                for area, total in stats_por_area
            ],
            'simulados_por_mes': [
                {'mes': mes, 'total': total} 
                for mes, total in simulados_por_mes
            ],
            'top_usuarios': [
                {'username': username, 'total_simulados': total} 
                for username, total in top_usuarios
            ],
            'distribuicao_notas': distribuicao_notas
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar estatísticas: {str(e)}'}), 500

@admin_bp.route('/admin/usuarios', methods=['GET'])
@admin_token_required
def get_usuarios(current_admin_id):
    """Lista todos os usuários com paginação"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        query = User.query
        
        if search:
            query = query.filter(
                db.or_(
                    User.username.contains(search),
                    User.email.contains(search)
                )
            )
        
        usuarios = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Adicionar estatísticas de cada usuário
        usuarios_data = []
        for user in usuarios.items:
            total_simulados = Simulado.query.filter_by(user_id=user.id).count()
            simulados_finalizados = Simulado.query.filter_by(
                user_id=user.id, 
                status='finalizado'
            ).count()
            
            # Última atividade
            ultimo_simulado = Simulado.query.filter_by(
                user_id=user.id
            ).order_by(desc(Simulado.data_criacao)).first()
            
            usuarios_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'data_criacao': user.data_criacao.isoformat() if user.data_criacao else None,
                'total_simulados': total_simulados,
                'simulados_finalizados': simulados_finalizados,
                'ultima_atividade': ultimo_simulado.data_criacao.isoformat() if ultimo_simulado else None
            })
        
        return jsonify({
            'usuarios': usuarios_data,
            'pagination': {
                'page': usuarios.page,
                'pages': usuarios.pages,
                'per_page': usuarios.per_page,
                'total': usuarios.total,
                'has_next': usuarios.has_next,
                'has_prev': usuarios.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar usuários: {str(e)}'}), 500

@admin_bp.route('/admin/simulados', methods=['GET'])
@admin_token_required
def get_simulados(current_admin_id):
    """Lista todos os simulados com paginação"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '')
        
        query = db.session.query(Simulado, User.username).join(User)
        
        if status:
            query = query.filter(Simulado.status == status)
        
        simulados = query.order_by(desc(Simulado.data_criacao)).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        simulados_data = []
        for simulado, username in simulados.items:
            # Buscar resultado se existir
            resultado = ResultadoSimulado.query.filter_by(simulado_id=simulado.id).first()
            
            simulados_data.append({
                'id': simulado.id,
                'usuario': username,
                'areas_selecionadas': simulado.areas_selecionadas,
                'total_questoes': simulado.total_questoes,
                'status': simulado.status,
                'data_criacao': simulado.data_criacao.isoformat(),
                'data_finalizacao': simulado.data_finalizacao.isoformat() if simulado.data_finalizacao else None,
                'tempo_total': simulado.tempo_total,
                'nota_geral': resultado.nota_geral if resultado else None,
                'acertos': resultado.total_acertos if resultado else None
            })
        
        return jsonify({
            'simulados': simulados_data,
            'pagination': {
                'page': simulados.page,
                'pages': simulados.pages,
                'per_page': simulados.per_page,
                'total': simulados.total,
                'has_next': simulados.has_next,
                'has_prev': simulados.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar simulados: {str(e)}'}), 500

@admin_bp.route('/admin/questoes/stats', methods=['GET'])
@admin_token_required
def get_questoes_stats(current_admin_id):
    """Estatísticas detalhadas das questões"""
    try:
        # Estatísticas por área e dificuldade
        stats_detalhadas = db.session.query(
            Questao.area_conhecimento,
            Questao.dificuldade,
            func.count(Questao.id).label('total')
        ).group_by(Questao.area_conhecimento, Questao.dificuldade).all()
        
        # Questões mais respondidas
        questoes_populares = db.session.query(
            Questao.id,
            Questao.area_conhecimento,
            Questao.dificuldade,
            func.count(RespostaSimulado.id).label('total_respostas')
        ).join(RespostaSimulado).group_by(Questao.id).order_by(
            desc('total_respostas')
        ).limit(10).all()
        
        # Taxa de acerto por área - versão simplificada
        try:
            taxa_acerto_area = []
            areas = ['Linguagens', 'Ciências Humanas', 'Ciências da Natureza', 'Matemática']
            for area in areas:
                total_respostas = db.session.query(RespostaSimulado).join(Questao).filter(
                    Questao.area_conhecimento == area
                ).count()
                
                if total_respostas > 0:
                    acertos = db.session.query(RespostaSimulado).join(Questao).filter(
                        Questao.area_conhecimento == area,
                        RespostaSimulado.resposta_usuario == Questao.resposta_correta
                    ).count()
                    
                    taxa = (acertos / total_respostas) * 100
                    taxa_acerto_area.append({
                        'area': area,
                        'taxa_acerto': round(taxa, 1)
                    })
        except Exception as e:
            taxa_acerto_area = []
        
        return jsonify({
            'stats_por_area_dificuldade': [
                {
                    'area': area,
                    'dificuldade': dificuldade,
                    'total': total
                }
                for area, dificuldade, total in stats_detalhadas
            ],
            'questoes_populares': [
                {
                    'questao_id': questao_id,
                    'area': area,
                    'dificuldade': dificuldade,
                    'total_respostas': total_respostas
                }
                for questao_id, area, dificuldade, total_respostas in questoes_populares
            ],
            'taxa_acerto_por_area': taxa_acerto_area
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar estatísticas das questões: {str(e)}'}), 500

@admin_bp.route('/admin/create-admin', methods=['POST'])
def create_admin():
    """Cria um novo administrador (apenas para setup inicial)"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['username', 'email', 'password', 'nome_completo']):
        return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
    
    # Verificar se já existe algum admin (para segurança)
    if Admin.query.count() > 0:
        return jsonify({'error': 'Administrador já existe. Use o login normal.'}), 403
    
    # Criar novo admin
    admin = Admin(
        username=data['username'],
        email=data['email'],
        nome_completo=data['nome_completo'],
        nivel_acesso='super_admin'
    )
    admin.set_password(data['password'])
    
    try:
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'message': 'Administrador criado com sucesso',
            'admin': admin.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar administrador: {str(e)}'}), 500

