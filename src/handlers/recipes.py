import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from mangum import Mangum
from models.types import RecipeCreate, RecipeUpdate
from services.recipes_service import RecipesService

app = FastAPI(title="Recipes API")
service = RecipesService()


@app.get("/api/v1/recipes")
def list_recipes(
    ingredient_id: Optional[str] = Query(None),
    nutritional_group: Optional[str] = Query(None),
):
    return service.list_recipes(ingredient_id, nutritional_group)


@app.post("/api/v1/recipes", status_code=201)
def create_recipe(body: RecipeCreate):
    return service.create_recipe(body.model_dump())


@app.get("/api/v1/recipes/{recipe_id}")
def get_recipe(recipe_id: str):
    item = service.get_recipe(recipe_id)
    if not item:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return item


@app.put("/api/v1/recipes/{recipe_id}")
def update_recipe(recipe_id: str, body: RecipeUpdate):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    item = service.update_recipe(recipe_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return item


@app.delete("/api/v1/recipes/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: str):
    if not service.delete_recipe(recipe_id):
        raise HTTPException(status_code=404, detail="Recipe not found")


handler = Mangum(app, lifespan="off")
