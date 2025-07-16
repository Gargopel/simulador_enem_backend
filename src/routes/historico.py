from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.simulado import Simulado, ResultadoSimulado
from datetime import datetime, timedelta

historico_bp = Blueprint('historico', __name__)

@historico_bp.route('/usuario/<int:user_id>/simulados', methods=['GET'])
def get_simulados_usuario(user_id):
    """Retorna todos os simulados de um usuário"""
    
    # Verificar se o usuário existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Buscar simulados do usuário
    simulados = Simulado.query.filter_by(user_id=user_id).order_by(Simulado.data_criacao.desc()).all()
    
    simulados_data = []
    for simulado in simulados:
        simulado_dict = simulado.to_dict()
        
        # Adicionar resultado se existir
        if simulado.resultado:
            simulado_dict['resultado'] = simulado.resultado.to_dict()
        
        simulados_data.append(simulado_dict)
    
    return jsonify({
        'usuario': user.to_dict(),
        'simulados': simulados_data,
        'total_simulados': len(simulados_data)
    })

@historico_bp.route('/usuario/<int:user_id>/estatisticas', methods=['GET'])
def get_estatisticas_usuario(user_id):
    """Retorna estatísticas gerais do usuário"""
    
    # Verificar se o usuário existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Buscar simulados finalizados do usuário
    simulados_finalizados = Simulado.query.filter_by(
        user_id=user_id, 
        finalizado=True
    ).all()
    
    if not simulados_finalizados:
        return jsonify({
            'usuario': user.to_dict(),
            'total_simulados': 0,
            'estatisticas': {
                'media_geral': 0,
                'melhor_nota': 0,
                'pior_nota': 0,
                'evolucao': [],
                'desempenho_por_area': {},
                'tempo_medio_prova': 0
            }
        })
    
    # Calcular estatísticas
    notas_gerais = []
    notas_por_area = {
        'linguagens': [],
        'ciencias_humanas': [],
        'ciencias_natureza': [],
        'matematica': []
    }
    tempos_prova = []
    evolucao = []
    
    for simulado in simulados_finalizados:
        if simulado.resultado:
            resultado = simulado.resultado
            
            # Nota geral
            if resultado.nota_geral:
                notas_gerais.append(resultado.nota_geral)
                evolucao.append({
                    'data': simulado.data_finalizacao.isoformat() if simulado.data_finalizacao else None,
                    'nota': resultado.nota_geral
                })
            
            # Notas por área
            if resultado.nota_linguagens:
                notas_por_area['linguagens'].append(resultado.nota_linguagens)
            if resultado.nota_ciencias_humanas:
                notas_por_area['ciencias_humanas'].append(resultado.nota_ciencias_humanas)
            if resultado.nota_ciencias_natureza:
                notas_por_area['ciencias_natureza'].append(resultado.nota_ciencias_natureza)
            if resultado.nota_matematica:
                notas_por_area['matematica'].append(resultado.nota_matematica)
        
        # Tempo de prova
        if simulado.tempo_total:
            tempos_prova.append(simulado.tempo_total)
    
    # Calcular médias e estatísticas
    media_geral = sum(notas_gerais) / len(notas_gerais) if notas_gerais else 0
    melhor_nota = max(notas_gerais) if notas_gerais else 0
    pior_nota = min(notas_gerais) if notas_gerais else 0
    tempo_medio = sum(tempos_prova) / len(tempos_prova) if tempos_prova else 0
    
    # Desempenho por área
    desempenho_por_area = {}
    areas_nomes = {
        'linguagens': 'Linguagens, Códigos e suas Tecnologias',
        'ciencias_humanas': 'Ciências Humanas e suas Tecnologias',
        'ciencias_natureza': 'Ciências da Natureza e suas Tecnologias',
        'matematica': 'Matemática e suas Tecnologias'
    }
    
    for area, notas in notas_por_area.items():
        if notas:
            desempenho_por_area[area] = {
                'nome': areas_nomes[area],
                'media': sum(notas) / len(notas),
                'melhor_nota': max(notas),
                'pior_nota': min(notas),
                'total_simulados': len(notas)
            }
    
    # Ordenar evolução por data
    evolucao.sort(key=lambda x: x['data'] if x['data'] else '')
    
    return jsonify({
        'usuario': user.to_dict(),
        'total_simulados': len(simulados_finalizados),
        'estatisticas': {
            'media_geral': round(media_geral, 1),
            'melhor_nota': round(melhor_nota, 1),
            'pior_nota': round(pior_nota, 1),
            'evolucao': evolucao,
            'desempenho_por_area': desempenho_por_area,
            'tempo_medio_prova': round(tempo_medio / 60, 1) if tempo_medio else 0  # Converter para minutos
        }
    })

@historico_bp.route('/resultado/<int:simulado_id>', methods=['GET'])
def get_resultado_detalhado(simulado_id):
    """Retorna resultado detalhado de um simulado específico"""
    
    # Buscar o simulado
    simulado = Simulado.query.get(simulado_id)
    if not simulado:
        return jsonify({'error': 'Simulado não encontrado'}), 404
    
    # Buscar o resultado
    resultado = ResultadoSimulado.query.filter_by(simulado_id=simulado_id).first()
    if not resultado:
        return jsonify({'error': 'Resultado não encontrado'}), 404
    
    # Buscar respostas detalhadas
    from src.models.simulado import RespostaSimulado
    respostas = RespostaSimulado.query.filter_by(simulado_id=simulado_id).all()
    
    respostas_detalhadas = []
    for resposta in respostas:
        if resposta.questao:
            resposta_dict = resposta.to_dict()
            resposta_dict['acertou'] = resposta.resposta_usuario == resposta.questao.resposta_correta
            respostas_detalhadas.append(resposta_dict)
    
    # Organizar respostas por área
    respostas_por_area = {}
    for resposta in respostas_detalhadas:
        area = resposta['questao']['area_conhecimento']
        if area not in respostas_por_area:
            respostas_por_area[area] = []
        respostas_por_area[area].append(resposta)
    
    return jsonify({
        'simulado': simulado.to_dict(),
        'resultado': resultado.to_dict(),
        'respostas_detalhadas': respostas_detalhadas,
        'respostas_por_area': respostas_por_area,
        'total_respostas': len(respostas_detalhadas)
    })

@historico_bp.route('/comparar-simulados', methods=['POST'])
def comparar_simulados():
    """Compara dois ou mais simulados do mesmo usuário"""
    
    data = request.get_json()
    if not data or 'simulados_ids' not in data:
        return jsonify({'error': 'IDs dos simulados são obrigatórios'}), 400
    
    simulados_ids = data['simulados_ids']
    
    if len(simulados_ids) < 2:
        return jsonify({'error': 'É necessário pelo menos 2 simulados para comparação'}), 400
    
    # Buscar simulados
    simulados = Simulado.query.filter(Simulado.id.in_(simulados_ids)).all()
    
    if len(simulados) != len(simulados_ids):
        return jsonify({'error': 'Alguns simulados não foram encontrados'}), 404
    
    # Verificar se todos são do mesmo usuário
    user_ids = set(s.user_id for s in simulados)
    if len(user_ids) > 1:
        return jsonify({'error': 'Todos os simulados devem ser do mesmo usuário'}), 400
    
    # Buscar resultados
    comparacao = []
    for simulado in simulados:
        if simulado.resultado:
            comparacao.append({
                'simulado_id': simulado.id,
                'data': simulado.data_finalizacao.isoformat() if simulado.data_finalizacao else None,
                'areas_selecionadas': simulado.get_areas_selecionadas(),
                'tempo_total': simulado.tempo_total,
                'resultado': simulado.resultado.to_dict()
            })
    
    # Calcular evolução
    if len(comparacao) >= 2:
        comparacao.sort(key=lambda x: x['data'] if x['data'] else '')
        
        evolucao_notas = {
            'linguagens': [],
            'ciencias_humanas': [],
            'ciencias_natureza': [],
            'matematica': [],
            'geral': []
        }
        
        for comp in comparacao:
            resultado = comp['resultado']
            evolucao_notas['linguagens'].append(resultado.get('nota_linguagens'))
            evolucao_notas['ciencias_humanas'].append(resultado.get('nota_ciencias_humanas'))
            evolucao_notas['ciencias_natureza'].append(resultado.get('nota_ciencias_natureza'))
            evolucao_notas['matematica'].append(resultado.get('nota_matematica'))
            evolucao_notas['geral'].append(resultado.get('nota_geral'))
        
        # Calcular tendências (melhoria/piora)
        tendencias = {}
        for area, notas in evolucao_notas.items():
            notas_validas = [n for n in notas if n is not None]
            if len(notas_validas) >= 2:
                primeira_nota = notas_validas[0]
                ultima_nota = notas_validas[-1]
                diferenca = ultima_nota - primeira_nota
                
                if diferenca > 10:
                    tendencia = 'melhoria'
                elif diferenca < -10:
                    tendencia = 'piora'
                else:
                    tendencia = 'estavel'
                
                tendencias[area] = {
                    'tendencia': tendencia,
                    'diferenca': round(diferenca, 1),
                    'primeira_nota': round(primeira_nota, 1),
                    'ultima_nota': round(ultima_nota, 1)
                }
    else:
        evolucao_notas = {}
        tendencias = {}
    
    return jsonify({
        'comparacao': comparacao,
        'evolucao_notas': evolucao_notas,
        'tendencias': tendencias,
        'total_simulados_comparados': len(comparacao)
    })

