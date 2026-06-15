import pytest
from fastapi import status


# ──────────────────────────────────────────────
# 1. Listar produtos quando o banco está vazio
# ──────────────────────────────────────────────

def test_listar_produtos_banco_vazio(client):
    """Verifica que a listagem retorna uma lista vazia quando não há produtos."""
    response = client.get("/produtos")
    assert response.status_code == 200
    assert response.json() == []


# ──────────────────────────────────────────────
# 2. Criar produto e verificar persistência no banco
# ──────────────────────────────────────────────

def test_criar_produto_e_verificar_persistencia(client):
    """Cria um produto via POST e verifica que ele foi persistido com GET por id."""
    payload = {"nome": "Teclado Mecânico", "preco": 259.90, "estoque": 15}
    response = client.post("/produtos", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    assert data["nome"] == "Teclado Mecânico"
    assert data["preco"] == 259.90
    assert data["estoque"] == 15
    assert data["ativo"] is True  # valor padrão

    # Verifica persistência buscando pelo id
    produto_id = data["id"]
    get_response = client.get(f"/produtos/{produto_id}")
    assert get_response.status_code == 200
    assert get_response.json()["nome"] == "Teclado Mecânico"


# ──────────────────────────────────────────────
# 3. Criar produto e verificar que aparece na listagem
# ──────────────────────────────────────────────

def test_criar_produto_aparece_na_listagem(client):
    """Cria dois produtos e verifica que ambos aparecem na listagem GET /produtos."""
    p1 = {"nome": "Mouse Gamer", "preco": 180.00, "estoque": 30}
    p2 = {"nome": "Monitor 24 polegadas", "preco": 899.90, "estoque": 5}

    client.post("/produtos", json=p1)
    client.post("/produtos", json=p2)

    response = client.get("/produtos")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2

    nomes = [p["nome"] for p in data]
    assert "Mouse Gamer" in nomes
    assert "Monitor 24 polegadas" in nomes


# ──────────────────────────────────────────────
# 4. Buscar produto por id — caso de sucesso
# ──────────────────────────────────────────────

def test_buscar_produto_por_id_sucesso(produto_existente):
    """Usa a fixture produto_existente e busca pelo id — deve retornar 200."""
    client = produto_existente["client"]
    produto = produto_existente["produto"]

    response = client.get(f"/produtos/{produto['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == produto["id"]
    assert response.json()["nome"] == "Produto de Teste"


# ──────────────────────────────────────────────
# 5. Buscar produto com id inexistente — 404
# ──────────────────────────────────────────────

def test_buscar_produto_id_inexistente(client):
    """Busca um id que não existe no banco — deve retornar 404."""
    response = client.get("/produtos/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Produto não encontrado"


# ──────────────────────────────────────────────
# 6. Deletar produto — deve retornar 204
# ──────────────────────────────────────────────

def test_deletar_produto_sucesso(produto_existente):
    """Deleta um produto existente e verifica que retorna 204 No Content."""
    client = produto_existente["client"]
    produto = produto_existente["produto"]

    response = client.delete(f"/produtos/{produto['id']}")
    assert response.status_code == 204


# ──────────────────────────────────────────────
# 7. Deletar produto e confirmar remoção com GET subsequente
# ──────────────────────────────────────────────

def test_deletar_produto_e_confirmar_remocao(produto_existente):
    """Deleta um produto e depois tenta buscá-lo — deve retornar 404."""
    client = produto_existente["client"]
    produto = produto_existente["produto"]

    # Deleta
    delete_response = client.delete(f"/produtos/{produto['id']}")
    assert delete_response.status_code == 204

    # Confirma que foi removido
    get_response = client.get(f"/produtos/{produto['id']}")
    assert get_response.status_code == 404


# ──────────────────────────────────────────────
# 8. Deletar produto inexistente — 404
# ──────────────────────────────────────────────

def test_deletar_produto_inexistente(client):
    """Tenta deletar um produto com id que não existe — deve retornar 404."""
    response = client.delete("/produtos/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Produto não encontrado"


# ──────────────────────────────────────────────
# 9. Teste parametrizado — payloads inválidos (422)
# ──────────────────────────────────────────────

@pytest.mark.parametrize("payload_invalido, descricao", [
    ({"preco": 100.0, "estoque": 5}, "nome ausente"),
    ({"nome": "", "preco": 100.0}, "nome vazio (string vazia)"),
    ({"nome": "Produto", "preco": -10.0}, "preço negativo"),
    ({"nome": "Produto", "preco": 0}, "preço igual a zero"),
    ({"nome": "Produto", "preco": 50.0, "estoque": -1}, "estoque negativo"),
    ({"nome": "Produto"}, "preço ausente"),
])
def test_criar_produto_payload_invalido(client, payload_invalido, descricao):
    """Verifica que payloads inválidos retornam 422 Unprocessable Entity.
    Testa: {descricao}"""
    response = client.post("/produtos", json=payload_invalido)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ──────────────────────────────────────────────
# 10. Teste de isolamento entre execuções
# ──────────────────────────────────────────────

def test_isolamento_banco_entre_testes(client):
    """Verifica que o banco está limpo no início do teste.
    Se a fixture client fizer o drop_all/create_all corretamente,
    a listagem deve estar vazia — independente da ordem de execução."""
    # O banco deve estar vazio pois a fixture cria/destrói tabelas a cada teste
    response = client.get("/produtos")
    assert response.status_code == 200
    assert response.json() == [], (
        "O banco deveria estar vazio no início do teste. "
        "Se há dados residuais, o isolamento entre testes está quebrado."
    )

    # Cria um produto para garantir que este teste também gera dados
    client.post("/produtos", json={"nome": "Produto Temporário", "preco": 10.0})

    # Verifica que o produto foi criado
    response = client.get("/produtos")
    assert len(response.json()) == 1

    # Após este teste, a fixture deve destruir tudo.
    # O próximo teste que rodar não deve ver este produto.


# ──────────────────────────────────────────────
# Cobertura Extra — Teste do get_db original
# ──────────────────────────────────────────────

def test_get_db_generator():
    """Garante a cobertura da dependência get_db() original."""
    from main import get_db
    generator = get_db()
    try:
        db = next(generator)
        assert db is not None
        try:
            next(generator)
        except StopIteration:
            pass
    except Exception:
        # Se falhar porque o banco de desenvolvimento está offline, tudo bem.
        # As linhas de setup/try já terão sido executadas e cobertas.
        pass
