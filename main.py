import os
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session


# ──────────────────────────────────────────────
# Configuração do Banco de Dados
# ──────────────────────────────────────────────

# Lê a URL do banco de dados da variável de ambiente
# Padrão: PostgreSQL local na porta 5432 (banco de desenvolvimento)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/produtos_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ──────────────────────────────────────────────
# Modelo SQLAlchemy — Produto
# ──────────────────────────────────────────────

class Produto(Base):
    """Modelo ORM que mapeia a tabela 'produtos' no PostgreSQL."""
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String, nullable=False)
    preco = Column(Float, nullable=False)
    estoque = Column(Integer, nullable=False, default=0)
    ativo = Column(Boolean, nullable=False, default=True)


# ──────────────────────────────────────────────
# Schemas Pydantic — Validação de Entrada e Saída
# ──────────────────────────────────────────────

class ProdutoCreate(BaseModel):
    """Schema para criação de produto (body do POST)."""
    nome: str = Field(..., min_length=1, description="Nome do produto — obrigatório, não pode ser vazio")
    preco: float = Field(..., gt=0, description="Preço em reais — obrigatório, deve ser maior que zero")
    estoque: int = Field(0, ge=0, description="Quantidade em estoque — padrão: 0")
    ativo: bool = Field(True, description="Se o produto está disponível para venda — padrão: True")


class ProdutoResponse(BaseModel):
    """Schema de resposta — inclui o id gerado pelo banco."""
    id: int
    nome: str
    preco: float
    estoque: int
    ativo: bool

    model_config = ConfigDict(from_attributes=True)  # Permite converter ORM → Pydantic



# ──────────────────────────────────────────────
# Dependency Injection — Sessão do Banco
# ──────────────────────────────────────────────

def get_db():
    """Injeta uma sessão do banco de dados em cada requisição.
    O yield garante que a sessão é fechada após o uso."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ──────────────────────────────────────────────
# Inicialização do FastAPI e Criação das Tabelas
# ──────────────────────────────────────────────

app = FastAPI(
    title="API de Gerenciamento de Produtos",
    description="API REST para gerenciar o catálogo de produtos de um e-commerce.",
    version="1.0.0",
)

# Cria as tabelas no banco de dados ao iniciar a aplicação (apenas se não estiver rodando testes com Pytest)
import sys
if "pytest" not in sys.modules:
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível criar tabelas no banco de desenvolvimento (PostgreSQL offline): {e}")


# ──────────────────────────────────────────────
# Endpoints da API — CRUD de Produtos
# ──────────────────────────────────────────────

@app.get("/produtos", response_model=List[ProdutoResponse], status_code=200)
def listar_produtos(db: Session = Depends(get_db)):
    """Retorna a lista de todos os produtos cadastrados."""
    produtos = db.query(Produto).all()
    return produtos


@app.post("/produtos", response_model=ProdutoResponse, status_code=201)
def criar_produto(produto: ProdutoCreate, db: Session = Depends(get_db)):
    """Cria um novo produto e retorna com o id gerado pelo banco."""
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
    """Retorna um produto pelo id ou 404 se não existir."""
    produto = db.query(Produto).filter(Produto.id == id).first()
    if produto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado",
        )
    return produto


@app.delete("/produtos/{id}", status_code=204)
def deletar_produto(id: int, db: Session = Depends(get_db)):
    """Remove um produto pelo id ou retorna 404 se não existir."""
    produto = db.query(Produto).filter(Produto.id == id).first()
    if produto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado",
        )
    db.delete(produto)
    db.commit()
    return None

