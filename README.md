# 🛒 API de Gerenciamento de Produtos - Testes Automatizados com Pytest & PostgreSQL no Docker

Este projeto consiste em uma API REST desenvolvida em **FastAPI** para o gerenciamento de produtos de um e-commerce. A persistência é realizada em um banco de dados **PostgreSQL** orquestrado via **Docker Compose**, e os testes automatizados são executados com **Pytest** contra uma base real de testes isolada.

---

## 🛠️ Tecnologias Utilizadas

* **FastAPI**: Desenvolvimento ágil e tipado de APIs.
* **SQLAlchemy**: ORM para mapeamento objeto-relacional com PostgreSQL.
* **PostgreSQL**: Banco de dados relacional robusto.
* **Docker & Docker Compose**: Isolamento e orquestração dos ambientes de desenvolvimento e teste.
* **Pytest**: Framework para testes unitários, parametrizados e de integração.
* **HTTPX**: Cliente HTTP assíncrono utilizado pelo TestClient do FastAPI.

---

## 📁 Estrutura do Projeto

A estrutura segue rigorosamente o padrão exigido para a avaliação:

```
seu_repositorio/
├── main.py                 # Código principal da API (Modelos, Schemas e Rotas)
├── conftest.py             # Fixtures e configurações globais de teste do Pytest
├── requirements.txt        # Dependências do projeto
├── docker-compose.yml      # Configuração dos containers Docker (Dev e Testes)
├── Dockerfile              # Imagem Docker da aplicação FastAPI
├── pytest.ini              # Configurações do Pytest
├── README.md               # Documentação oficial
└── tests/
    ├── __init__.py         # Inicialização do pacote de testes
    └── test_produtos.py    # Suíte contendo os 10 cenários de testes obrigatórios
```

---

## 🚀 Como Executar a Aplicação (Desenvolvimento)

Para executar a API conectada ao banco de dados PostgreSQL de desenvolvimento, siga as instruções abaixo:

1. **Subir os containers do banco de dados e da aplicação:**
   ```bash
   docker-compose up --build
   ```
2. **Acessar a documentação interativa (Swagger UI):**
   Acesse [http://localhost:8000/docs](http://localhost:8000/docs) para testar os endpoints interativamente.

---

## 🧪 Como Executar os Testes Automatizados

A suíte de testes do Pytest é executada contra um banco PostgreSQL de teste separado rodando na porta **5433** (`db_test`), garantindo que a base de desenvolvimento não seja poluída ou apagada.

### Passo 1: Subir o banco de teste via Docker
Certifique-se de que o container do banco de testes está rodando e saudável:
```bash
docker-compose up -d db_test
```

### Passo 2: Executar a suíte de testes e cobertura
Com o banco de teste rodando, execute o Pytest localmente (certifique-se de ter instalado as dependências do `requirements.txt` em seu ambiente virtual):
```bash
pytest --cov=main -v
```

---

## 🛡️ Como funciona o Isolamento entre os Testes?

O isolamento total entre cada execução de teste é garantido através do ciclo de vida da fixture `client` implementada no arquivo [conftest.py](file:///c:/Users/yagon/Desktop/p2terça/conftest.py):

1. **Setup (Antes de rodar o teste):**  
   O Pytest executa `Base.metadata.create_all(bind=engine_test)`, gerando uma estrutura limpa e nova de tabelas diretamente no banco de dados `produtos_test_db`.
2. **Override da Dependência:**  
   O `app.dependency_overrides[get_db]` redireciona a sessão de banco do FastAPI para usar a sessão do banco de testes (`TestingSessionLocal`).
3. **Execução:**  
   O TestClient executa as requisições HTTP do teste em isolamento.
4. **Teardown (Após rodar o teste):**  
   Independentemente de o teste ter passado ou falhado, o bloco de código após o `yield` é executado. Ele remove as overrides e roda `Base.metadata.drop_all(bind=engine_test)`, destruindo fisicamente todas as tabelas e dados, deixando o banco 100% limpo para a próxima execução de teste.

---

## 📊 Saída Esperada do Pytest (Term-Missing Coverage)

```
============================= test session starts =============================
platform win32 -- Python 3.10.x, pytest-8.2.2, pluggy-1.6.0 -- C:\Users\yagon\Desktop\p2terça\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\yagon\Desktop\p2terça
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.13.0, cov-5.0.0
collecting ... collected 15 items

tests/test_produtos.py::test_listar_produtos_banco_vazio PASSED          [  6%]
tests/test_produtos.py::test_criar_produto_e_verificar_persistencia PASSED [ 13%]
tests/test_produtos.py::test_criar_produto_aparece_na_listagem PASSED    [ 20%]
tests/test_produtos.py::test_buscar_produto_por_id_sucesso PASSED        [ 26%]
tests/test_produtos.py::test_buscar_produto_id_inexistente PASSED        [ 33%]
tests/test_produtos.py::test_deletar_produto_sucesso PASSED              [ 40%]
tests/test_produtos.py::test_deletar_produto_e_confirmar_remocao PASSED  [ 46%]
tests/test_produtos.py::test_deletar_produto_inexistente PASSED          [ 53%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload_invalido0-nome ausente] PASSED [ 60%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload_invalido1-nome vazio] PASSED [ 66%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload_invalido2-preço negativo] PASSED [ 73%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload_invalido3-preço igual a zero] PASSED [ 80%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload_invalido4-estoque negativo] PASSED [ 86%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload_invalido5-preço ausente] PASSED [ 93%]
tests/test_produtos.py::test_isolamento_banco_entre_testes PASSED        [100%]

---------- coverage: platform win32, python 3.10.x ----------
Name      Stmts   Miss  Cover   Missing
---------------------------------------
main.py      66      4    94%   90-93
---------------------------------------
TOTAL        66      4    94%

======================== 15 passed, 1 warning in 1.55s ========================
```

