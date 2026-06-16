import os
import sys
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Configuração do Banco de Dados
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/produtos_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo do Produto
class Produto(Base):
    """Modelo ORM para a tabela de produtos."""
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String, nullable=False)
    preco = Column(Float, nullable=False)
    estoque = Column(Integer, nullable=False, default=0)
    ativo = Column(Boolean, nullable=False, default=True)

# Schemas Pydantic (Validação de Entrada e Saída)
class ProdutoCreate(BaseModel):
    nome: str = Field(..., min_length=1, description="Nome do produto (obrigatório, não vazio)")
    preco: float = Field(..., gt=0, description="Preço em reais (obrigatório, maior que zero)")
    estoque: int = Field(0, ge=0, description="Quantidade em estoque (padrão: 0)")
    ativo: bool = Field(True, description="Produto ativo para venda")

class ProdutoResponse(BaseModel):
    id: int
    nome: str
    preco: float
    estoque: int
    ativo: bool

    model_config = ConfigDict(from_attributes=True)

# Dependency Injection da sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Inicialização do FastAPI
app = FastAPI(
    title="API de Gerenciamento de Produtos",
    description="API para gerenciamento de catálogo de produtos.",
    version="1.0.0",
)

# Cria as tabelas se não estiver rodando testes
if "pytest" not in sys.modules:
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Aviso: Banco de desenvolvimento offline: {e}")

# Endpoints - CRUD de Produtos
@app.get("/produtos", response_model=List[ProdutoResponse], status_code=200)
def listar_produtos(db: Session = Depends(get_db)):
    return db.query(Produto).all()

@app.post("/produtos", response_model=ProdutoResponse, status_code=201)
def criar_produto(produto: ProdutoCreate, db: Session = Depends(get_db)):
    novo_produto = Produto(
        nome=produto.nome,
        preco=produto.preco,
        estoque=produto.estoque,
        ativo=produto.ativo,
    )
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)
    return novo_produto

@app.get("/produtos/{id}", response_model=ProdutoResponse, status_code=200)
def obter_produto(id: int, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == id).first()
    if produto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado",
        )
    return produto

@app.delete("/produtos/{id}", status_code=204)
def deletar_produto(id: int, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == id).first()
    if produto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado",
        )
    db.delete(produto)
    db.commit()
    return None
