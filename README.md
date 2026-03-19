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
# Start DynamoDB Local
docker-compose up -d

# Install dependencies
pip install -r requirements-dev.txt

# Copy env file
cp .env.example .env

# Start local server
uvicorn local_server:app --reload --port 3001
```

API available at http://localhost:3001/api/v1

### API Endpoints

**Ingredients**
- `GET    /api/v1/ingredients` — list all (optional `?nutritional_group=X`)
- `POST   /api/v1/ingredients` — create
- `GET    /api/v1/ingredients/{id}` — get one
- `PUT    /api/v1/ingredients/{id}` — update
- `DELETE /api/v1/ingredients/{id}` — delete

**Recipes**
- `GET    /api/v1/recipes` — list all (optional `?ingredient_id=X&nutritional_group=Y`)
- `POST   /api/v1/recipes` — create (with ingredients array)
- `GET    /api/v1/recipes/{id}` — get one (populated)
- `PUT    /api/v1/recipes/{id}` — update
- `DELETE /api/v1/recipes/{id}` — delete

**Meal Plans**
- `GET    /api/v1/meal-plans` — list all
- `POST   /api/v1/meal-plans` — create
- `GET    /api/v1/meal-plans/{id}` — get one (with entries)
- `PUT    /api/v1/meal-plans/{id}` — update
- `DELETE /api/v1/meal-plans/{id}` — delete
- `POST   /api/v1/meal-plans/{id}/entries` — add entry
- `GET    /api/v1/meal-plans/{id}/meal-list` — ordered meal list
- `GET    /api/v1/meal-plans/{id}/grocery-list` — grocery list `{ required, optional }`

## Deployment

Uses AWS SAM:
```bash
sam build
sam deploy --guided
```
