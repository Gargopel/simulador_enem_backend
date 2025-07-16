import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.user import db
from src.models.questao import Questao
from src.main import app
import random

def criar_questoes_exemplo():
    """Cria questões de exemplo para testar o sistema"""
    
    questoes_exemplo = [
        # Linguagens
        {
            'area_conhecimento': 'Linguagens',
            'disciplina': 'Português',
            'ano_prova': 2023,
            'caderno_prova': 'Azul',
            'numero_questao': 1,
            'enunciado': '''
            <p>Leia o texto a seguir:</p>
            <p><em>"A linguagem é um sistema de signos que permite a comunicação entre os seres humanos. Ela é fundamental para a construção do conhecimento e para a interação social."</em></p>
            <p>Com base no texto, é correto afirmar que a linguagem:</p>
            ''',
            'alternativas': [
                'É apenas um meio de comunicação verbal.',
                'Serve exclusivamente para transmitir informações.',
                'É um sistema complexo que vai além da simples comunicação.',
                'Não tem relação com a construção do conhecimento.',
                'É utilizada apenas em contextos formais.'
            ],
            'resposta_correta': 'C',
            'nivel_dificuldade': 'facil'
        },
        {
            'area_conhecimento': 'Linguagens',
            'disciplina': 'Literatura',
            'ano_prova': 2023,
            'caderno_prova': 'Azul',
            'numero_questao': 2,
            'enunciado': '''
            <p>O Romantismo brasileiro teve características próprias que o diferenciaram do movimento europeu. Uma dessas características foi:</p>
            ''',
            'alternativas': [
                'A valorização exclusiva da cultura europeia.',
                'O indianismo como forma de buscar uma identidade nacional.',
                'A rejeição completa aos sentimentos e emoções.',
                'O foco apenas em temas urbanos e industriais.',
                'A ausência de elementos da natureza brasileira.'
            ],
            'resposta_correta': 'B',
            'nivel_dificuldade': 'medio'
        },
        
        # Ciências Humanas
        {
            'area_conhecimento': 'Ciências Humanas',
            'disciplina': 'História',
            'ano_prova': 2023,
            'caderno_prova': 'Azul',
            'numero_questao': 3,
            'enunciado': '''
            <p>A Revolução Industrial, iniciada na Inglaterra no século XVIII, trouxe profundas transformações sociais e econômicas. Uma das principais consequências desse processo foi:</p>
            ''',
            'alternativas': [
                'A manutenção do sistema feudal.',
                'O fortalecimento da economia agrícola.',
                'O surgimento da classe operária urbana.',
                'A diminuição da população nas cidades.',
                'O fim do comércio internacional.'
            ],
            'resposta_correta': 'C',
            'nivel_dificuldade': 'facil'
        },
        {
            'area_conhecimento': 'Ciências Humanas',
            'disciplina': 'Geografia',
            'ano_prova': 2023,
            'caderno_prova': 'Azul',
            'numero_questao': 4,
            'enunciado': '''
            <p>O processo de urbanização no Brasil intensificou-se a partir da segunda metade do século XX. Esse fenômeno está relacionado principalmente a:</p>
            ''',
            'alternativas': [
                'Políticas de incentivo à agricultura familiar.',
                'Migração rural-urbana em busca de oportunidades de trabalho.',
                'Diminuição da população brasileira.',
                'Desenvolvimento exclusivo do setor primário.',
                'Redução das atividades industriais.'
            ],
            'resposta_correta': 'B',
            'nivel_dificuldade': 'medio'
        },
        
        # Ciências da Natureza
        {
            'area_conhecimento': 'Ciências da Natureza',
            'disciplina': 'Física',
            'ano_prova': 2023,
            'caderno_prova': 'Azul',
            'numero_questao': 5,
            'enunciado': '''
            <p>Um objeto é lançado verticalmente para cima com velocidade inicial de 20 m/s. Considerando g = 10 m/s² e desprezando a resistência do ar, o tempo que o objeto leva para retornar ao ponto de lançamento é:</p>
            ''',
            'alternativas': [
                '1 segundo',
                '2 segundos',
                '3 segundos',
                '4 segundos',
                '5 segundos'
            ],
            'resposta_correta': 'D',
            'nivel_dificuldade': 'medio'
        },
        {
            'area_conhecimento': 'Ciências da Natureza',
            'disciplina': 'Química',
            'ano_prova': 2023,
            'caderno_prova': 'Azul',
            'numero_questao': 6,
            'enunciado': '''
            <p>A água (H₂O) é uma substância fundamental para a vida. Em relação às suas propriedades, é correto afirmar que:</p>
            ''',
            'alternativas': [
                'É uma molécula apolar.',
                'Possui alta tensão superficial devido às ligações de hidrogênio.',
                'Não pode dissolver substâncias iônicas.',
                'Tem ponto de ebulição baixo em relação à sua massa molecular.',
                'É formada por ligações covalentes apolares.'
            ],
            'resposta_correta': 'B',
            'nivel_dificuldade': 'dificil'
        },
        {
            'area_conhecimento': 'Ciências da Natureza',
            'disciplina': 'Biologia',
            'ano_prova': 2023,
            'caderno_prova': 'Azul',
            'numero_questao': 7,
            'enunciado': '''
            <p>A fotossíntese é um processo fundamental para a manutenção da vida na Terra. Durante esse processo:</p>
            ''',
            'alternativas': [
                'Apenas oxigênio é produzido.',
                'Energia luminosa é convertida em energia química.',
                'Apenas dióxido de carbono é consumido.',
                'Não há produção de glicose.',
                'Ocorre apenas durante a noite.'
            ],
            'resposta_correta': 'B',
            'nivel_dificuldade': 'facil'
        },
        
        # Matemática
        {
            'area_conhecimento': 'Matemática',
            'disciplina': 'Matemática',
            'ano_prova': 2023,
            'caderno_prova': 'Azul',
            'numero_questao': 8,
            'enunciado': '''
            <p>Uma função do primeiro grau é definida por f(x) = 2x + 3. O valor de f(5) é:</p>
            ''',
            'alternativas': [
                '8',
                '10',
                '11',
                '13',
                '15'
            ],
            'resposta_correta': 'D',
            'nivel_dificuldade': 'facil'
        },
        {
            'area_conhecimento': 'Matemática',
            'disciplina': 'Matemática',
            'ano_prova': 2023,
            'caderno_prova': 'Azul',
            'numero_questao': 9,
            'enunciado': '''
            <p>Em um triângulo retângulo, os catetos medem 3 cm e 4 cm. A medida da hipotenusa é:</p>
            ''',
            'alternativas': [
                '5 cm',
                '6 cm',
                '7 cm',
                '8 cm',
                '9 cm'
            ],
            'resposta_correta': 'A',
            'nivel_dificuldade': 'medio'
        },
        {
            'area_conhecimento': 'Matemática',
            'disciplina': 'Matemática',
            'ano_prova': 2023,
            'caderno_prova': 'Azul',
            'numero_questao': 10,
            'enunciado': '''
            <p>A equação x² - 5x + 6 = 0 tem como soluções:</p>
            ''',
            'alternativas': [
                'x = 1 e x = 6',
                'x = 2 e x = 3',
                'x = -2 e x = -3',
                'x = 0 e x = 5',
                'x = 1 e x = 5'
            ],
            'resposta_correta': 'B',
            'nivel_dificuldade': 'dificil'
        }
    ]
    
    # Criar mais questões para cada área (para ter pelo menos 45 por área)
    questoes_completas = []
    
    for area in ['Linguagens', 'Ciências Humanas', 'Ciências da Natureza', 'Matemática']:
        questoes_area = [q for q in questoes_exemplo if q['area_conhecimento'] == area]
        
        # Replicar e modificar questões para ter 45 por área
        for i in range(45):
            if i < len(questoes_area):
                questao = questoes_area[i].copy()
            else:
                # Usar uma questão base e modificar
                questao_base = questoes_area[i % len(questoes_area)].copy()
                questao = questao_base.copy()
                questao['numero_questao'] = i + 1
                
                # Variar a dificuldade
                dificuldades = ['facil', 'medio', 'dificil']
                questao['nivel_dificuldade'] = random.choice(dificuldades)
                
                # Modificar ligeiramente o enunciado
                questao['enunciado'] = questao['enunciado'].replace('questão', f'questão {i+1}')
            
            questoes_completas.append(questao)
    
    return questoes_completas

def popular_banco():
    """Popula o banco de dados com questões de exemplo"""
    
    with app.app_context():
        # Limpar questões existentes
        Questao.query.delete()
        
        questoes = criar_questoes_exemplo()
        
        for questao_data in questoes:
            questao = Questao(
                area_conhecimento=questao_data['area_conhecimento'],
                disciplina=questao_data['disciplina'],
                ano_prova=questao_data['ano_prova'],
                caderno_prova=questao_data['caderno_prova'],
                numero_questao=questao_data['numero_questao'],
                enunciado=questao_data['enunciado'],
                resposta_correta=questao_data['resposta_correta'],
                nivel_dificuldade=questao_data['nivel_dificuldade']
            )
            
            questao.set_alternativas(questao_data['alternativas'])
            db.session.add(questao)
        
        db.session.commit()
        
        # Verificar quantas questões foram criadas
        total_questoes = Questao.query.count()
        questoes_por_area = {}
        
        for area in ['Linguagens', 'Ciências Humanas', 'Ciências da Natureza', 'Matemática']:
            count = Questao.query.filter_by(area_conhecimento=area).count()
            questoes_por_area[area] = count
        
        print(f"✅ Banco populado com sucesso!")
        print(f"📊 Total de questões: {total_questoes}")
        print("📋 Questões por área:")
        for area, count in questoes_por_area.items():
            print(f"   - {area}: {count} questões")
        
        print("\n🎯 Distribuição por dificuldade:")
        for dificuldade in ['facil', 'medio', 'dificil']:
            count = Questao.query.filter_by(nivel_dificuldade=dificuldade).count()
            print(f"   - {dificuldade.capitalize()}: {count} questões")

if __name__ == '__main__':
    popular_banco()

