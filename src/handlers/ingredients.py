import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from mangum import Mangum
from models.types import IngredientCreate, IngredientUpdate
from services.ingredients_service import IngredientsService

app = FastAPI(title="Ingredients API")
service = IngredientsService()


@app.get("/api/v1/ingredients")
def list_ingredients(nutritional_group: Optional[str] = Query(None)):
    return service.list_ingredients(nutritional_group)


@app.post("/api/v1/ingredients", status_code=201)
def create_ingredient(body: IngredientCreate):
    return service.create_ingredient(body.model_dump())


@app.get("/api/v1/ingredients/{ingredient_id}")
def get_ingredient(ingredient_id: str):
    item = service.get_ingredient(ingredient_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return item


@app.put("/api/v1/ingredients/{ingredient_id}")
def update_ingredient(ingredient_id: str, body: IngredientUpdate):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    item = service.update_ingredient(ingredient_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return item


@app.delete("/api/v1/ingredients/{ingredient_id}", status_code=204)
def delete_ingredient(ingredient_id: str):
    if not service.delete_ingredient(ingredient_id):
        raise HTTPException(status_code=404, detail="Ingredient not found")


handler = Mangum(app, lifespan="off")
