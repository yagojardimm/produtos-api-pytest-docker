import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from main import app, Base, get_db

# Banco de dados de teste (PostgreSQL na porta 5433)
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/produtos_test_db"

engine_test = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

@pytest.fixture
def client():
    # Setup: cria tabelas no banco de teste
    Base.metadata.create_all(bind=engine_test)

    # Injeta a sessão de testes no app
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    # Teardown: limpa overrides e dropa tabelas (isolamento)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine_test)

@pytest.fixture
def produto_existente(client):
    """Auxiliar para testes que dependem de um produto já cadastrado."""
    payload = {
        "nome": "Produto de Teste",
        "preco": 49.90,
        "estoque": 10,
        "ativo": True,
    }
    response = client.post("/produtos", json=payload)
    dados = response.json()
    return {"client": client, "produto": dados}
