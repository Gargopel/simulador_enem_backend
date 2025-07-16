from src.models.user import db
import json

class Questao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area_conhecimento = db.Column(db.String(100), nullable=False)  # Linguagens, Ciências Humanas, Ciências da Natureza, Matemática
    disciplina = db.Column(db.String(50), nullable=False)  # Português, História, Física, etc.
    ano_prova = db.Column(db.Integer, nullable=False)
    caderno_prova = db.Column(db.String(20), nullable=False)  # Azul, Amarelo, Branco, Rosa
    numero_questao = db.Column(db.Integer, nullable=False)
    enunciado = db.Column(db.Text, nullable=False)
    alternativas = db.Column(db.Text, nullable=False)  # JSON string com as 5 alternativas
    resposta_correta = db.Column(db.String(1), nullable=False)  # A, B, C, D, E
    nivel_dificuldade = db.Column(db.String(10), nullable=False)  # facil, medio, dificil
    competencias_habilidades = db.Column(db.Text)  # JSON string opcional
    resolucao_comentada = db.Column(db.Text)  # Opcional

    def __repr__(self):
        return f'<Questao {self.id} - {self.area_conhecimento} - {self.ano_prova}>'

    def to_dict(self):
        return {
            'id': self.id,
            'area_conhecimento': self.area_conhecimento,
            'disciplina': self.disciplina,
            'ano_prova': self.ano_prova,
            'caderno_prova': self.caderno_prova,
            'numero_questao': self.numero_questao,
            'enunciado': self.enunciado,
            'alternativas': json.loads(self.alternativas) if self.alternativas else [],
            'resposta_correta': self.resposta_correta,
            'nivel_dificuldade': self.nivel_dificuldade,
            'competencias_habilidades': json.loads(self.competencias_habilidades) if self.competencias_habilidades else [],
            'resolucao_comentada': self.resolucao_comentada
        }

    def set_alternativas(self, alternativas_list):
        """Define as alternativas como JSON string"""
        self.alternativas = json.dumps(alternativas_list)

    def get_alternativas(self):
        """Retorna as alternativas como lista"""
        return json.loads(self.alternativas) if self.alternativas else []

    def set_competencias_habilidades(self, competencias_list):
        """Define as competências e habilidades como JSON string"""
        self.competencias_habilidades = json.dumps(competencias_list)

    def get_competencias_habilidades(self):
        """Retorna as competências e habilidades como lista"""
        return json.loads(self.competencias_habilidades) if self.competencias_habilidades else []

