import pytest
from fastapi import status

# Listar produtos com o banco vazio
def test_listar_produtos_banco_vazio(client):
    response = client.get("/produtos")
    assert response.status_code == 200
    assert response.json() == []

# Criar produto e validar persistência
def test_criar_produto_e_verificar_persistencia(client):
    payload = {"nome": "Teclado Mecânico", "preco": 259.90, "estoque": 15}
    response = client.post("/produtos", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    assert data["nome"] == "Teclado Mecânico"
    assert data["preco"] == 259.90
    assert data["estoque"] == 15
    assert data["ativo"] is True

    # Valida persistência buscando por ID
    produto_id = data["id"]
    get_response = client.get(f"/produtos/{produto_id}")
    assert get_response.status_code == 200
    assert get_response.json()["nome"] == "Teclado Mecânico"

# Validar se o produto criado aparece na listagem geral
def test_criar_produto_aparece_na_listagem(client):
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

# Buscar produto existente por ID
def test_buscar_produto_por_id_sucesso(produto_existente):
    client = produto_existente["client"]
    produto = produto_existente["produto"]

    response = client.get(f"/produtos/{produto['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == produto["id"]
    assert response.json()["nome"] == "Produto de Teste"

# Buscar produto inexistente (404)
def test_buscar_produto_id_inexistente(client):
    response = client.get("/produtos/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Produto não encontrado"

# Exclusão de produto (204)
def test_deletar_produto_sucesso(produto_existente):
    client = produto_existente["client"]
    produto = produto_existente["produto"]

    response = client.delete(f"/produtos/{produto['id']}")
    assert response.status_code == 204

# Confirmar remoção após delete
def test_deletar_produto_e_confirmar_remocao(produto_existente):
    client = produto_existente["client"]
    produto = produto_existente["produto"]

    # Deleta o produto
    delete_response = client.delete(f"/produtos/{produto['id']}")
    assert delete_response.status_code == 204

    # Valida que o GET retorna 404 agora
    get_response = client.get(f"/produtos/{produto['id']}")
    assert get_response.status_code == 404

# Deletar produto inexistente (404)
def test_deletar_produto_inexistente(client):
    response = client.delete("/produtos/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Produto não encontrado"

# Validação de payloads inválidos (422)
@pytest.mark.parametrize("payload_invalido, descricao", [
    ({"preco": 100.0, "estoque": 5}, "nome ausente"),
    ({"nome": "", "preco": 100.0}, "nome vazio"),
    ({"nome": "Produto", "preco": -10.0}, "preço negativo"),
    ({"nome": "Produto", "preco": 0}, "preço igual a zero"),
    ({"nome": "Produto", "preco": 50.0, "estoque": -1}, "estoque negativo"),
    ({"nome": "Produto"}, "preço ausente"),
])
def test_criar_produto_payload_invalido(client, payload_invalido, descricao):
    response = client.post("/produtos", json=payload_invalido)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# Validação de isolamento do banco entre execuções
def test_isolamento_banco_entre_testes(client):
    # O banco deve começar vazio mesmo após outras execuções
    response = client.get("/produtos")
    assert response.status_code == 200
    assert response.json() == []

    # Insere dado temporário
    client.post("/produtos", json={"nome": "Temporário", "preco": 10.0})

    # Confirma inserção
    response = client.get("/produtos")
    assert len(response.json()) == 1
