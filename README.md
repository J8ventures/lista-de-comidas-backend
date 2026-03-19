# Recipe Manager — Backend

Python Lambda handlers + FastAPI local server, behind AWS API Gateway.

## Stack
- Python 3.12
- boto3 (DynamoDB)
- Pydantic v2 (validation)
- FastAPI (local dev server)
- Mangum (ASGI adapter for Lambda)
- AWS SAM (deployment)

## Local Development

### Prerequisites
- Docker & Docker Compose
- Python 3.12+
- AWS SAM CLI (optional, for Lambda testing)

### Setup
```bash
# Activate the shared virtual environment (from the project root)
source ../venv/bin/activate

# Start DynamoDB Local
docker-compose up -d

# Copy env file
cp .env.example .env

# Start local server
uvicorn local_server:app --reload --port 3001
```

API available at http://localhost:3001/api/v1

### Running tests

Tests use `pytest` and mock all DynamoDB calls, so **no running services are needed**.

```bash
# From the backend/ directory, with the venv activated:
pytest

# Verbose output
pytest -v

# Single test file
pytest tests/test_ingredients_service.py -v
```

**Test structure:**
- `tests/test_ingredients_service.py` — unit tests for `IngredientsService` (repositories mocked)
- `tests/test_recipes_service.py` — unit tests for `RecipesService` (repositories mocked)
- `tests/test_meal_plans_service.py` — unit tests for `MealPlansService` (repositories + sub-services mocked)
- `tests/test_api.py` — HTTP-layer integration tests for all routes (services mocked via `monkeypatch`)

### API Endpoints

**Ingredientes**
- `GET    /api/v1/ingredientes` — listar todos (opcional `?grupo_nutricional=X`)
- `POST   /api/v1/ingredientes` — crear
- `GET    /api/v1/ingredientes/{id}` — obtener uno
- `PUT    /api/v1/ingredientes/{id}` — actualizar
- `DELETE /api/v1/ingredientes/{id}` — eliminar

**Recetas**
- `GET    /api/v1/recetas` — listar todas (opcional `?id_ingrediente=X&grupo_nutricional=Y`)
- `POST   /api/v1/recetas` — crear (con array de ingredientes)
- `GET    /api/v1/recetas/{id}` — obtener una (con ingredientes poblados)
- `PUT    /api/v1/recetas/{id}` — actualizar
- `DELETE /api/v1/recetas/{id}` — eliminar

**Planes de comida**
- `GET    /api/v1/planes-comida` — listar todos
- `POST   /api/v1/planes-comida` — crear
- `GET    /api/v1/planes-comida/{id}` — obtener uno (con entradas)
- `PUT    /api/v1/planes-comida/{id}` — actualizar
- `DELETE /api/v1/planes-comida/{id}` — eliminar
- `POST   /api/v1/planes-comida/{id}/entradas` — agregar entrada
- `GET    /api/v1/planes-comida/{id}/lista-comidas` — lista de comidas ordenada
- `GET    /api/v1/planes-comida/{id}/lista-compras` — lista de compras `{ requeridos, opcionales }`

## Deployment

Uses AWS SAM:
```bash
sam build
sam deploy --guided
```
