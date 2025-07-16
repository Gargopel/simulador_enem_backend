from src.models.user import db
from datetime import datetime
import json

class Simulado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    areas_selecionadas = db.Column(db.Text, nullable=False)  # JSON string com as áreas selecionadas
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_finalizacao = db.Column(db.DateTime)
    tempo_total = db.Column(db.Integer)  # Tempo em segundos
    finalizado = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    user = db.relationship('User', backref=db.backref('simulados', lazy=True))
    respostas = db.relationship('RespostaSimulado', backref='simulado', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Simulado {self.id} - User {self.user_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'areas_selecionadas': json.loads(self.areas_selecionadas) if self.areas_selecionadas else [],
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_finalizacao': self.data_finalizacao.isoformat() if self.data_finalizacao else None,
            'tempo_total': self.tempo_total,
            'finalizado': self.finalizado
        }

    def set_areas_selecionadas(self, areas_list):
        """Define as áreas selecionadas como JSON string"""
        self.areas_selecionadas = json.dumps(areas_list)

    def get_areas_selecionadas(self):
        """Retorna as áreas selecionadas como lista"""
        return json.loads(self.areas_selecionadas) if self.areas_selecionadas else []

class RespostaSimulado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    simulado_id = db.Column(db.Integer, db.ForeignKey('simulado.id'), nullable=False)
    questao_id = db.Column(db.Integer, db.ForeignKey('questao.id'), nullable=False)
    resposta_usuario = db.Column(db.String(1))  # A, B, C, D, E ou None se não respondida
    tempo_resposta = db.Column(db.Integer)  # Tempo em segundos para responder a questão
    
    # Relacionamentos
    questao = db.relationship('Questao', backref=db.backref('respostas', lazy=True))

    def __repr__(self):
        return f'<RespostaSimulado {self.id} - Simulado {self.simulado_id} - Questão {self.questao_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'simulado_id': self.simulado_id,
            'questao_id': self.questao_id,
            'resposta_usuario': self.resposta_usuario,
            'tempo_resposta': self.tempo_resposta,
            'questao': self.questao.to_dict() if self.questao else None
        }

class ResultadoSimulado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    simulado_id = db.Column(db.Integer, db.ForeignKey('simulado.id'), nullable=False, unique=True)
    nota_linguagens = db.Column(db.Float)
    nota_ciencias_humanas = db.Column(db.Float)
    nota_ciencias_natureza = db.Column(db.Float)
    nota_matematica = db.Column(db.Float)
    nota_geral = db.Column(db.Float)
    acertos_linguagens = db.Column(db.Integer, default=0)
    acertos_ciencias_humanas = db.Column(db.Integer, default=0)
    acertos_ciencias_natureza = db.Column(db.Integer, default=0)
    acertos_matematica = db.Column(db.Integer, default=0)
    total_questoes_linguagens = db.Column(db.Integer, default=0)
    total_questoes_ciencias_humanas = db.Column(db.Integer, default=0)
    total_questoes_ciencias_natureza = db.Column(db.Integer, default=0)
    total_questoes_matematica = db.Column(db.Integer, default=0)
    dicas_estudo = db.Column(db.Text)  # JSON string com dicas personalizadas
    
    # Relacionamento
    simulado = db.relationship('Simulado', backref=db.backref('resultado', uselist=False))

    def __repr__(self):
        return f'<ResultadoSimulado {self.id} - Simulado {self.simulado_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'simulado_id': self.simulado_id,
            'nota_linguagens': self.nota_linguagens,
            'nota_ciencias_humanas': self.nota_ciencias_humanas,
            'nota_ciencias_natureza': self.nota_ciencias_natureza,
            'nota_matematica': self.nota_matematica,
            'nota_geral': self.nota_geral,
            'acertos_linguagens': self.acertos_linguagens,
            'acertos_ciencias_humanas': self.acertos_ciencias_humanas,
            'acertos_ciencias_natureza': self.acertos_ciencias_natureza,
            'acertos_matematica': self.acertos_matematica,
            'total_questoes_linguagens': self.total_questoes_linguagens,
            'total_questoes_ciencias_humanas': self.total_questoes_ciencias_humanas,
            'total_questoes_ciencias_natureza': self.total_questoes_ciencias_natureza,
            'total_questoes_matematica': self.total_questoes_matematica,
            'dicas_estudo': json.loads(self.dicas_estudo) if self.dicas_estudo else []
        }

    def set_dicas_estudo(self, dicas_list):
        """Define as dicas de estudo como JSON string"""
        self.dicas_estudo = json.dumps(dicas_list)

    def get_dicas_estudo(self):
        """Retorna as dicas de estudo como lista"""
        return json.loads(self.dicas_estudo) if self.dicas_estudo else []

