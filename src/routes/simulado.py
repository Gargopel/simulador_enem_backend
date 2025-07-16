from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.questao import Questao
from src.models.simulado import Simulado, RespostaSimulado, ResultadoSimulado
import random
import math
from datetime import datetime

simulado_bp = Blueprint('simulado', __name__)

@simulado_bp.route('/areas-conhecimento', methods=['GET'])
def get_areas_conhecimento():
    """Retorna as áreas de conhecimento disponíveis"""
    areas = [
        {
            'id': 'linguagens',
            'nome': 'Linguagens, Códigos e suas Tecnologias',
            'descricao': 'Língua Portuguesa, Literatura, Língua Estrangeira, Artes, Educação Física e Tecnologias da Informação'
        },
        {
            'id': 'ciencias_humanas',
            'nome': 'Ciências Humanas e suas Tecnologias',
            'descricao': 'História, Geografia, Filosofia e Sociologia'
        },
        {
            'id': 'ciencias_natureza',
            'nome': 'Ciências da Natureza e suas Tecnologias',
            'descricao': 'Química, Física e Biologia'
        },
        {
            'id': 'matematica',
            'nome': 'Matemática e suas Tecnologias',
            'descricao': 'Matemática e suas aplicações'
        }
    ]
    return jsonify(areas)

@simulado_bp.route('/criar-simulado', methods=['POST'])
def criar_simulado():
    """Cria um novo simulado com questões aleatórias das áreas selecionadas"""
    data = request.get_json()
    
    if not data or 'user_id' not in data or 'areas_selecionadas' not in data:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    user_id = data['user_id']
    areas_selecionadas = data['areas_selecionadas']
    
    # Verificar se o usuário existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Criar o simulado
    simulado = Simulado(user_id=user_id)
    simulado.set_areas_selecionadas(areas_selecionadas)
    
    db.session.add(simulado)
    db.session.commit()
    
    # Gerar questões aleatórias para cada área selecionada
    questoes_simulado = []
    
    for area in areas_selecionadas:
        # Mapear área para o nome no banco de dados
        area_map = {
            'linguagens': 'Linguagens',
            'ciencias_humanas': 'Ciências Humanas',
            'ciencias_natureza': 'Ciências da Natureza',
            'matematica': 'Matemática'
        }
        
        area_nome = area_map.get(area)
        if not area_nome:
            continue
            
        # Buscar questões da área (45 questões por área como no ENEM real)
        questoes_area = Questao.query.filter_by(area_conhecimento=area_nome).all()
        
        if len(questoes_area) >= 45:
            questoes_selecionadas = random.sample(questoes_area, 45)
        else:
            # Se não tiver 45 questões, usar todas disponíveis
            questoes_selecionadas = questoes_area
        
        # Criar respostas vazias para cada questão
        for questao in questoes_selecionadas:
            resposta = RespostaSimulado(
                simulado_id=simulado.id,
                questao_id=questao.id
            )
            db.session.add(resposta)
            questoes_simulado.append(questao.to_dict())
    
    db.session.commit()
    
    return jsonify({
        'simulado_id': simulado.id,
        'questoes': questoes_simulado,
        'total_questoes': len(questoes_simulado)
    })

@simulado_bp.route('/simulado/<int:simulado_id>', methods=['GET'])
def get_simulado(simulado_id):
    """Retorna os dados de um simulado específico"""
    simulado = Simulado.query.get(simulado_id)
    if not simulado:
        return jsonify({'error': 'Simulado não encontrado'}), 404
    
    # Buscar as questões do simulado
    respostas = RespostaSimulado.query.filter_by(simulado_id=simulado_id).all()
    questoes = [resposta.questao.to_dict() for resposta in respostas if resposta.questao]
    
    return jsonify({
        'simulado': simulado.to_dict(),
        'questoes': questoes,
        'total_questoes': len(questoes)
    })

@simulado_bp.route('/responder-questao', methods=['POST'])
def responder_questao():
    """Salva a resposta de uma questão do simulado"""
    data = request.get_json()
    
    if not data or 'simulado_id' not in data or 'questao_id' not in data:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    simulado_id = data['simulado_id']
    questao_id = data['questao_id']
    resposta_usuario = data.get('resposta_usuario')
    tempo_resposta = data.get('tempo_resposta')
    
    # Buscar a resposta existente
    resposta = RespostaSimulado.query.filter_by(
        simulado_id=simulado_id,
        questao_id=questao_id
    ).first()
    
    if not resposta:
        return jsonify({'error': 'Questão não encontrada no simulado'}), 404
    
    # Atualizar a resposta
    resposta.resposta_usuario = resposta_usuario
    resposta.tempo_resposta = tempo_resposta
    
    db.session.commit()
    
    return jsonify({'message': 'Resposta salva com sucesso'})

@simulado_bp.route('/finalizar-simulado', methods=['POST'])
def finalizar_simulado():
    """Finaliza o simulado e calcula as notas"""
    data = request.get_json()
    
    if not data or 'simulado_id' not in data:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    simulado_id = data['simulado_id']
    tempo_total = data.get('tempo_total', 0)
    
    # Buscar o simulado
    simulado = Simulado.query.get(simulado_id)
    if not simulado:
        return jsonify({'error': 'Simulado não encontrado'}), 404
    
    # Marcar como finalizado
    simulado.finalizado = True
    simulado.data_finalizacao = datetime.utcnow()
    simulado.tempo_total = tempo_total
    
    # Calcular as notas
    resultado = calcular_notas_simulado(simulado_id)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Simulado finalizado com sucesso',
        'resultado': resultado.to_dict() if resultado else None
    })

def calcular_notas_simulado(simulado_id):
    """Calcula as notas do simulado usando uma versão simplificada da TRI"""
    
    # Buscar todas as respostas do simulado
    respostas = RespostaSimulado.query.filter_by(simulado_id=simulado_id).all()
    
    # Organizar respostas por área
    areas_respostas = {
        'Linguagens': [],
        'Ciências Humanas': [],
        'Ciências da Natureza': [],
        'Matemática': []
    }
    
    for resposta in respostas:
        if resposta.questao:
            area = resposta.questao.area_conhecimento
            if area in areas_respostas:
                areas_respostas[area].append(resposta)
    
    # Calcular notas para cada área
    notas = {}
    acertos = {}
    totais = {}
    
    for area, respostas_area in areas_respostas.items():
        if not respostas_area:
            continue
            
        acertos_area = 0
        total_questoes = len(respostas_area)
        
        # Contar acertos
        for resposta in respostas_area:
            if resposta.resposta_usuario == resposta.questao.resposta_correta:
                acertos_area += 1
        
        # Calcular nota usando TRI simplificada
        nota_area = calcular_nota_tri_simplificada(respostas_area, acertos_area, total_questoes)
        
        # Mapear nomes das áreas
        area_key = {
            'Linguagens': 'linguagens',
            'Ciências Humanas': 'ciencias_humanas',
            'Ciências da Natureza': 'ciencias_natureza',
            'Matemática': 'matematica'
        }.get(area, area.lower())
        
        notas[area_key] = nota_area
        acertos[area_key] = acertos_area
        totais[area_key] = total_questoes
    
    # Calcular nota geral (média das áreas)
    nota_geral = sum(notas.values()) / len(notas) if notas else 0
    
    # Criar ou atualizar resultado
    resultado = ResultadoSimulado.query.filter_by(simulado_id=simulado_id).first()
    if not resultado:
        resultado = ResultadoSimulado(simulado_id=simulado_id)
        db.session.add(resultado)
    
    # Atualizar dados do resultado
    resultado.nota_linguagens = notas.get('linguagens')
    resultado.nota_ciencias_humanas = notas.get('ciencias_humanas')
    resultado.nota_ciencias_natureza = notas.get('ciencias_natureza')
    resultado.nota_matematica = notas.get('matematica')
    resultado.nota_geral = nota_geral
    
    resultado.acertos_linguagens = acertos.get('linguagens', 0)
    resultado.acertos_ciencias_humanas = acertos.get('ciencias_humanas', 0)
    resultado.acertos_ciencias_natureza = acertos.get('ciencias_natureza', 0)
    resultado.acertos_matematica = acertos.get('matematica', 0)
    
    resultado.total_questoes_linguagens = totais.get('linguagens', 0)
    resultado.total_questoes_ciencias_humanas = totais.get('ciencias_humanas', 0)
    resultado.total_questoes_ciencias_natureza = totais.get('ciencias_natureza', 0)
    resultado.total_questoes_matematica = totais.get('matematica', 0)
    
    # Gerar dicas de estudo
    dicas = gerar_dicas_estudo(notas, acertos, totais)
    resultado.set_dicas_estudo(dicas)
    
    return resultado

def calcular_nota_tri_simplificada(respostas_area, acertos, total_questoes):
    """
    Calcula uma nota usando uma versão simplificada da TRI
    Considera a dificuldade das questões e a coerência das respostas
    """
    if total_questoes == 0:
        return 0
    
    # Pesos por dificuldade (simulando a TRI)
    pesos_dificuldade = {
        'facil': 1.0,
        'medio': 1.5,
        'dificil': 2.0
    }
    
    pontos_obtidos = 0
    pontos_maximos = 0
    
    # Calcular pontos considerando dificuldade
    for resposta in respostas_area:
        questao = resposta.questao
        peso = pesos_dificuldade.get(questao.nivel_dificuldade, 1.0)
        pontos_maximos += peso
        
        if resposta.resposta_usuario == questao.resposta_correta:
            pontos_obtidos += peso
    
    # Calcular percentual de acerto ponderado
    if pontos_maximos > 0:
        percentual_acerto = pontos_obtidos / pontos_maximos
    else:
        percentual_acerto = 0
    
    # Aplicar penalidade por inconsistência (TRI simplificada)
    penalidade = calcular_penalidade_inconsistencia(respostas_area)
    percentual_final = max(0, percentual_acerto - penalidade)
    
    # Converter para escala do ENEM (aproximadamente 200-1000)
    nota_final = 200 + (percentual_final * 800)
    
    return round(nota_final, 1)

def calcular_penalidade_inconsistencia(respostas_area):
    """
    Calcula penalidade por inconsistência nas respostas
    (acertar difícil e errar fácil é penalizado)
    """
    acertos_facil = 0
    erros_facil = 0
    acertos_dificil = 0
    erros_dificil = 0
    
    for resposta in respostas_area:
        questao = resposta.questao
        acertou = resposta.resposta_usuario == questao.resposta_correta
        
        if questao.nivel_dificuldade == 'facil':
            if acertou:
                acertos_facil += 1
            else:
                erros_facil += 1
        elif questao.nivel_dificuldade == 'dificil':
            if acertou:
                acertos_dificil += 1
            else:
                erros_dificil += 1
    
    # Penalidade por acertar difícil e errar fácil
    penalidade = 0
    if acertos_dificil > 0 and erros_facil > 0:
        # Quanto mais questões fáceis erradas em relação às difíceis acertadas, maior a penalidade
        ratio_inconsistencia = erros_facil / (acertos_dificil + 1)
        penalidade = min(0.2, ratio_inconsistencia * 0.1)  # Máximo 20% de penalidade
    
    return penalidade

def gerar_dicas_estudo(notas, acertos, totais):
    """Gera dicas de estudo personalizadas baseadas no desempenho"""
    dicas = []
    
    areas_nomes = {
        'linguagens': 'Linguagens, Códigos e suas Tecnologias',
        'ciencias_humanas': 'Ciências Humanas e suas Tecnologias',
        'ciencias_natureza': 'Ciências da Natureza e suas Tecnologias',
        'matematica': 'Matemática e suas Tecnologias'
    }
    
    # Analisar desempenho por área
    for area, nota in notas.items():
        if area not in totais or totais[area] == 0:
            continue
            
        percentual_acerto = (acertos[area] / totais[area]) * 100
        area_nome = areas_nomes.get(area, area)
        
        if percentual_acerto < 40:
            dicas.append({
                'area': area_nome,
                'nivel': 'critico',
                'dica': f'Seu desempenho em {area_nome} precisa de atenção urgente. Recomendamos revisar os conceitos básicos e fazer exercícios fundamentais.',
                'sugestoes': [
                    'Revisar teoria básica da área',
                    'Fazer exercícios de fixação',
                    'Buscar videoaulas explicativas',
                    'Criar resumos dos principais conceitos'
                ]
            })
        elif percentual_acerto < 60:
            dicas.append({
                'area': area_nome,
                'nivel': 'atencao',
                'dica': f'Seu desempenho em {area_nome} está abaixo da média. Foque em praticar mais questões e revisar os tópicos com maior dificuldade.',
                'sugestoes': [
                    'Identificar tópicos com mais erros',
                    'Praticar questões de nível médio',
                    'Revisar questões erradas',
                    'Estudar em grupos ou com professores'
                ]
            })
        elif percentual_acerto < 80:
            dicas.append({
                'area': area_nome,
                'nivel': 'bom',
                'dica': f'Bom desempenho em {area_nome}! Continue praticando para aperfeiçoar ainda mais seus conhecimentos.',
                'sugestoes': [
                    'Praticar questões de nível avançado',
                    'Revisar questões que errou',
                    'Aprofundar conhecimentos específicos',
                    'Ajudar colegas com dificuldades'
                ]
            })
        else:
            dicas.append({
                'area': area_nome,
                'nivel': 'excelente',
                'dica': f'Excelente desempenho em {area_nome}! Mantenha o ritmo de estudos e foque nas outras áreas.',
                'sugestoes': [
                    'Manter o nível de estudos',
                    'Resolver questões desafiadoras',
                    'Ensinar outros estudantes',
                    'Focar em outras áreas que precisam de melhoria'
                ]
            })
    
    # Dica geral baseada na nota geral
    nota_geral = sum(notas.values()) / len(notas) if notas else 0
    
    if nota_geral < 500:
        dicas.append({
            'area': 'Geral',
            'nivel': 'critico',
            'dica': 'Sua nota geral indica necessidade de um plano de estudos mais intensivo. Considere buscar ajuda profissional.',
            'sugestoes': [
                'Criar cronograma de estudos estruturado',
                'Buscar aulas particulares ou cursinhos',
                'Dedicar mais horas diárias aos estudos',
                'Fazer simulados regularmente'
            ]
        })
    elif nota_geral < 600:
        dicas.append({
            'area': 'Geral',
            'nivel': 'atencao',
            'dica': 'Você está no caminho certo! Continue estudando com disciplina e foque nas áreas com menor desempenho.',
            'sugestoes': [
                'Manter regularidade nos estudos',
                'Priorizar áreas com menor nota',
                'Fazer mais simulados',
                'Revisar conteúdos sistematicamente'
            ]
        })
    else:
        dicas.append({
            'area': 'Geral',
            'nivel': 'bom',
            'dica': 'Parabéns! Você está bem preparado. Continue praticando para manter o alto desempenho.',
            'sugestoes': [
                'Manter rotina de estudos',
                'Focar em questões mais desafiadoras',
                'Revisar periodicamente todos os conteúdos',
                'Ajudar outros estudantes'
            ]
        })
    
    return dicas

