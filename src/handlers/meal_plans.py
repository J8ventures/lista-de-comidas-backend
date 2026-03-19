import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, HTTPException
from mangum import Mangum
from models.types import MealPlanCreate, MealPlanUpdate, MealPlanEntryCreate
from services.meal_plans_service import MealPlansService

app = FastAPI(title="Meal Plans API")
service = MealPlansService()


@app.get("/api/v1/meal-plans")
def list_meal_plans():
    return service.list_meal_plans()


@app.post("/api/v1/meal-plans", status_code=201)
def create_meal_plan(body: MealPlanCreate):
    return service.create_meal_plan(body.model_dump())


@app.get("/api/v1/meal-plans/{plan_id}")
def get_meal_plan(plan_id: str):
    item = service.get_meal_plan(plan_id)
    if not item:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return item


@app.put("/api/v1/meal-plans/{plan_id}")
def update_meal_plan(plan_id: str, body: MealPlanUpdate):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    item = service.update_meal_plan(plan_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return item


@app.delete("/api/v1/meal-plans/{plan_id}", status_code=204)
def delete_meal_plan(plan_id: str):
    if not service.delete_meal_plan(plan_id):
        raise HTTPException(status_code=404, detail="Meal plan not found")


@app.post("/api/v1/meal-plans/{plan_id}/entries", status_code=201)
def add_entry(plan_id: str, body: MealPlanEntryCreate):
    try:
        entry = service.add_entry(plan_id, body.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not entry:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return entry


@app.get("/api/v1/meal-plans/{plan_id}/meal-list")
def get_meal_list(plan_id: str):
    plan = service.get_meal_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return service.get_meal_list(plan_id)


@app.get("/api/v1/meal-plans/{plan_id}/grocery-list")
def get_grocery_list(plan_id: str):
    plan = service.get_meal_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return service.get_grocery_list(plan_id)


handler = Mangum(app, lifespan="off")
