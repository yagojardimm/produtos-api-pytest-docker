import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from main import app, Base, get_db

# ──────────────────────────────────────────────
# Banco de Teste — PostgreSQL na porta 5433
# Conecta ao banco PostgreSQL de teste provisionado via Docker (db_test)
# ──────────────────────────────────────────────

SQLALCHEMY_DATABASE_URL_TEST = "postgresql://postgres:postgres@localhost:5433/produtos_test_db"

engine_test = create_engine(SQLALCHEMY_DATABASE_URL_TEST)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


# ──────────────────────────────────────────────
# Fixture: client
# ──────────────────────────────────────────────

@pytest.fixture()
def client():
    # Setup — cria todas as tabelas no banco de teste
    Base.metadata.create_all(bind=engine_test)

    # Substitui a dependência get_db pela sessão de teste
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Entrega o TestClient para o teste
    yield TestClient(app)

    # Teardown — destrói todas as tabelas (isolamento total entre testes)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine_test)


# ──────────────────────────────────────────────
# Fixture auxiliar: produto_existente
# ──────────────────────────────────────────────

@pytest.fixture()
def produto_existente(client):
    """Cria um produto no banco e retorna os dados dele (dict) junto com o client."""
    payload = {
        "nome": "Produto de Teste",
        "preco": 49.90,
        "estoque": 10,
        "ativo": True,
    }
    response = client.post("/produtos", json=payload)
    dados = response.json()
    return {"client": client, "produto": dados}
