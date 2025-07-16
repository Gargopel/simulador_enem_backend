from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.questao import Questao
from src.models.admin import Admin
from src.routes.admin import admin_token_required
from sqlalchemy import func
import json

questoes_bp = Blueprint('questoes', __name__)

@questoes_bp.route('/admin/questoes', methods=['GET'])
@admin_token_required
def listar_questoes(current_admin_id):
    """Lista questões com paginação e filtros"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        area = request.args.get('area', '')
        disciplina = request.args.get('disciplina', '')
        dificuldade = request.args.get('dificuldade', '')
        search = request.args.get('search', '')

        # Query base
        query = Questao.query

        # Aplicar filtros
        if area:
            query = query.filter(Questao.area_conhecimento == area)
        if disciplina:
            query = query.filter(Questao.disciplina == disciplina)
        if dificuldade:
            query = query.filter(Questao.dificuldade == dificuldade)
        if search:
            query = query.filter(
                db.or_(
                    Questao.enunciado.contains(search),
                    Questao.disciplina.contains(search)
                )
            )

        # Paginação
        questoes_paginadas = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

        questoes = []
        for questao in questoes_paginadas.items:
            questao_dict = questao.to_dict()
            # Truncar enunciado para listagem
            if len(questao_dict['enunciado']) > 200:
                questao_dict['enunciado_resumido'] = questao_dict['enunciado'][:200] + '...'
            else:
                questao_dict['enunciado_resumido'] = questao_dict['enunciado']
            questoes.append(questao_dict)

        return jsonify({
            'questoes': questoes,
            'pagination': {
                'page': questoes_paginadas.page,
                'pages': questoes_paginadas.pages,
                'per_page': questoes_paginadas.per_page,
                'total': questoes_paginadas.total,
                'has_next': questoes_paginadas.has_next,
                'has_prev': questoes_paginadas.has_prev
            }
        })

    except Exception as e:
        return jsonify({'error': f'Erro ao listar questões: {str(e)}'}), 500

@questoes_bp.route('/admin/questoes', methods=['POST'])
@admin_token_required
def criar_questao(current_admin_id):
    """Cria uma nova questão"""
    try:
        data = request.get_json()

        # Validar dados obrigatórios
        required_fields = ['enunciado', 'alternativas', 'resposta_correta', 
                          'area_conhecimento', 'disciplina', 'dificuldade']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400

        # Validar alternativas
        alternativas = data['alternativas']
        if not isinstance(alternativas, list) or len(alternativas) != 5:
            return jsonify({'error': 'Deve haver exatamente 5 alternativas'}), 400

        # Validar resposta correta
        resposta_correta = data['resposta_correta'].upper()
        if resposta_correta not in ['A', 'B', 'C', 'D', 'E']:
            return jsonify({'error': 'Resposta correta deve ser A, B, C, D ou E'}), 400

        # Validar área de conhecimento
        areas_validas = ['Linguagens', 'Ciências Humanas', 'Ciências da Natureza', 'Matemática']
        if data['area_conhecimento'] not in areas_validas:
            return jsonify({'error': 'Área de conhecimento inválida'}), 400

        # Validar dificuldade
        dificuldades_validas = ['Facil', 'Medio', 'Dificil']
        if data['dificuldade'] not in dificuldades_validas:
            return jsonify({'error': 'Dificuldade deve ser Facil, Medio ou Dificil'}), 400

        # Criar questão
        nova_questao = Questao(
            enunciado=data['enunciado'],
            alternativas=json.dumps(alternativas),
            resposta_correta=resposta_correta,
            area_conhecimento=data['area_conhecimento'],
            disciplina=data['disciplina'],
            dificuldade=data['dificuldade'],
            explicacao=data.get('explicacao', ''),
            fonte=data.get('fonte', ''),
            ano=data.get('ano', None)
        )

        db.session.add(nova_questao)
        db.session.commit()

        return jsonify({
            'message': 'Questão criada com sucesso',
            'questao': nova_questao.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar questão: {str(e)}'}), 500

@questoes_bp.route('/admin/questoes/<int:questao_id>', methods=['GET'])
@admin_token_required
def obter_questao(current_admin_id, questao_id):
    """Obtém uma questão específica"""
    try:
        questao = Questao.query.get_or_404(questao_id)
        return jsonify({'questao': questao.to_dict()})
    except Exception as e:
        return jsonify({'error': f'Erro ao obter questão: {str(e)}'}), 500

@questoes_bp.route('/admin/questoes/<int:questao_id>', methods=['PUT'])
@admin_token_required
def atualizar_questao(current_admin_id, questao_id):
    """Atualiza uma questão existente"""
    try:
        questao = Questao.query.get_or_404(questao_id)
        data = request.get_json()

        # Atualizar campos se fornecidos
        if 'enunciado' in data:
            questao.enunciado = data['enunciado']
        
        if 'alternativas' in data:
            alternativas = data['alternativas']
            if not isinstance(alternativas, list) or len(alternativas) != 5:
                return jsonify({'error': 'Deve haver exatamente 5 alternativas'}), 400
            questao.alternativas = json.dumps(alternativas)
        
        if 'resposta_correta' in data:
            resposta_correta = data['resposta_correta'].upper()
            if resposta_correta not in ['A', 'B', 'C', 'D', 'E']:
                return jsonify({'error': 'Resposta correta deve ser A, B, C, D ou E'}), 400
            questao.resposta_correta = resposta_correta
        
        if 'area_conhecimento' in data:
            areas_validas = ['Linguagens', 'Ciências Humanas', 'Ciências da Natureza', 'Matemática']
            if data['area_conhecimento'] not in areas_validas:
                return jsonify({'error': 'Área de conhecimento inválida'}), 400
            questao.area_conhecimento = data['area_conhecimento']
        
        if 'disciplina' in data:
            questao.disciplina = data['disciplina']
        
        if 'dificuldade' in data:
            dificuldades_validas = ['Facil', 'Medio', 'Dificil']
            if data['dificuldade'] not in dificuldades_validas:
                return jsonify({'error': 'Dificuldade deve ser Facil, Medio ou Dificil'}), 400
            questao.dificuldade = data['dificuldade']
        
        if 'explicacao' in data:
            questao.explicacao = data['explicacao']
        
        if 'fonte' in data:
            questao.fonte = data['fonte']
        
        if 'ano' in data:
            questao.ano = data['ano']

        db.session.commit()

        return jsonify({
            'message': 'Questão atualizada com sucesso',
            'questao': questao.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar questão: {str(e)}'}), 500

@questoes_bp.route('/admin/questoes/<int:questao_id>', methods=['DELETE'])
@admin_token_required
def deletar_questao(current_admin_id, questao_id):
    """Deleta uma questão"""
    try:
        questao = Questao.query.get_or_404(questao_id)
        
        # Verificar se a questão não está sendo usada em simulados ativos
        # (implementar verificação se necessário)
        
        db.session.delete(questao)
        db.session.commit()

        return jsonify({'message': 'Questão deletada com sucesso'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao deletar questão: {str(e)}'}), 500

@questoes_bp.route('/admin/questoes/estatisticas', methods=['GET'])
@admin_token_required
def estatisticas_questoes(current_admin_id):
    """Retorna estatísticas das questões"""
    try:
        # Total por área
        stats_por_area = db.session.query(
            Questao.area_conhecimento,
            func.count(Questao.id).label('total')
        ).group_by(Questao.area_conhecimento).all()

        # Total por dificuldade
        stats_por_dificuldade = db.session.query(
            Questao.dificuldade,
            func.count(Questao.id).label('total')
        ).group_by(Questao.dificuldade).all()

        # Total por disciplina (top 10)
        stats_por_disciplina = db.session.query(
            Questao.disciplina,
            func.count(Questao.id).label('total')
        ).group_by(Questao.disciplina).order_by(func.count(Questao.id).desc()).limit(10).all()

        return jsonify({
            'total_questoes': Questao.query.count(),
            'por_area': [{'area': area, 'total': total} for area, total in stats_por_area],
            'por_dificuldade': [{'dificuldade': dif, 'total': total} for dif, total in stats_por_dificuldade],
            'por_disciplina': [{'disciplina': disc, 'total': total} for disc, total in stats_por_disciplina]
        })

    except Exception as e:
        return jsonify({'error': f'Erro ao obter estatísticas: {str(e)}'}), 500

@questoes_bp.route('/admin/questoes/import', methods=['POST'])
@admin_token_required
def importar_questoes(current_admin_id):
    """Importa questões em lote"""
    try:
        data = request.get_json()
        questoes_data = data.get('questoes', [])
        
        if not questoes_data:
            return jsonify({'error': 'Nenhuma questão fornecida'}), 400

        questoes_criadas = 0
        erros = []

        for i, questao_data in enumerate(questoes_data):
            try:
                # Validar dados obrigatórios
                required_fields = ['enunciado', 'alternativas', 'resposta_correta', 
                                  'area_conhecimento', 'disciplina', 'dificuldade']
                
                for field in required_fields:
                    if field not in questao_data or not questao_data[field]:
                        raise ValueError(f'Campo {field} é obrigatório')

                # Criar questão
                nova_questao = Questao(
                    enunciado=questao_data['enunciado'],
                    alternativas=json.dumps(questao_data['alternativas']),
                    resposta_correta=questao_data['resposta_correta'].upper(),
                    area_conhecimento=questao_data['area_conhecimento'],
                    disciplina=questao_data['disciplina'],
                    dificuldade=questao_data['dificuldade'],
                    explicacao=questao_data.get('explicacao', ''),
                    fonte=questao_data.get('fonte', ''),
                    ano=questao_data.get('ano', None)
                )

                db.session.add(nova_questao)
                questoes_criadas += 1

            except Exception as e:
                erros.append(f'Questão {i+1}: {str(e)}')

        if questoes_criadas > 0:
            db.session.commit()

        return jsonify({
            'message': f'{questoes_criadas} questões importadas com sucesso',
            'questoes_criadas': questoes_criadas,
            'erros': erros
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao importar questões: {str(e)}'}), 500

