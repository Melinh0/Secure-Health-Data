from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Paciente(Base):
    __tablename__ = "pacientes"
    id = Column(Integer, primary_key=True, index=True)
    nome_anon = Column(String, nullable=False)          # Nome anonimizado
    data_nascimento = Column(DateTime, nullable=True)
    sexo = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    exames = relationship("Exame", back_populates="paciente", cascade="all, delete-orphan")
    anotacoes = relationship("AnotacaoClinica", back_populates="paciente", cascade="all, delete-orphan")

class Exame(Base):
    __tablename__ = "exames"
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    data_coleta = Column(DateTime, nullable=False)
    exame_nome = Column(String, index=True, nullable=False)
    valor = Column(Float)
    unidade = Column(String, nullable=True)
    referencia_min = Column(Float, nullable=True)
    referencia_max = Column(Float, nullable=True)
    
    paciente = relationship("Paciente", back_populates="exames")
    
    __table_args__ = (
        Index("idx_paciente_data", "paciente_id", "data_coleta"),
        Index("idx_exame_nome", "exame_nome"),
    )

class AnotacaoClinica(Base):
    __tablename__ = "anotacoes"
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    data = Column(DateTime, nullable=False, default=datetime.utcnow)
    texto = Column(Text, nullable=False)
    tipo = Column(String, nullable=True)  # 'queixa', 'sintoma', 'evolucao', 'prescricao', 'conduta'
    
    paciente = relationship("Paciente", back_populates="anotacoes")