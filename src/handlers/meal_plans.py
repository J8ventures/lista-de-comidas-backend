import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from models.types import EntradaPlanCrear, PlanComidaActualizar, PlanComidaCrear
from services.meal_plans_service import MealPlansService

app = FastAPI(title="Planes de Comida API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
service = MealPlansService()


@app.get("/api/v1/planes-comida")
def listar_planes_comida():
    return service.list_meal_plans()


@app.post("/api/v1/planes-comida", status_code=201)
def crear_plan_comida(body: PlanComidaCrear):
    return service.create_meal_plan(body.model_dump())


@app.get("/api/v1/planes-comida/{id_plan}")
def obtener_plan_comida(id_plan: str):
    item = service.get_meal_plan(id_plan)
    if not item:
        raise HTTPException(status_code=404, detail="Plan de comida no encontrado")
    return item


@app.put("/api/v1/planes-comida/{id_plan}")
def actualizar_plan_comida(id_plan: str, body: PlanComidaActualizar):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    item = service.update_meal_plan(id_plan, data)
    if not item:
        raise HTTPException(status_code=404, detail="Plan de comida no encontrado")
    return item


@app.delete("/api/v1/planes-comida/{id_plan}", status_code=204)
def eliminar_plan_comida(id_plan: str):
    if not service.delete_meal_plan(id_plan):
        raise HTTPException(status_code=404, detail="Plan de comida no encontrado")


@app.post("/api/v1/planes-comida/{id_plan}/entradas", status_code=201)
def agregar_entrada(id_plan: str, body: EntradaPlanCrear):
    try:
        entrada = service.add_entry(id_plan, body.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    if not entrada:
        raise HTTPException(status_code=404, detail="Plan de comida no encontrado")
    return entrada


@app.get("/api/v1/planes-comida/{id_plan}/lista-comidas")
def obtener_lista_comidas(id_plan: str):
    plan = service.get_meal_plan(id_plan)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de comida no encontrado")
    return service.get_meal_list(id_plan)


@app.get("/api/v1/planes-comida/{id_plan}/lista-compras")
def obtener_lista_compras(id_plan: str):
    plan = service.get_meal_plan(id_plan)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de comida no encontrado")
    return service.get_grocery_list(id_plan)


handler = Mangum(app, lifespan="off")
