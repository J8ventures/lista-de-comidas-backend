import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from models.types import IngredienteActualizar, IngredienteCrear
from services.ingredients_service import IngredientsService

app = FastAPI(title="Ingredientes API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
service = IngredientsService()


@app.get("/api/v1/ingredientes")
def listar_ingredientes(grupo_nutricional: str | None = Query(None)):
    return service.list_ingredients(grupo_nutricional)


@app.post("/api/v1/ingredientes", status_code=201)
def crear_ingrediente(body: IngredienteCrear):
    return service.create_ingredient(body.model_dump())


@app.get("/api/v1/ingredientes/{id_ingrediente}")
def obtener_ingrediente(id_ingrediente: str):
    item = service.get_ingredient(id_ingrediente)
    if not item:
        raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
    return item


@app.put("/api/v1/ingredientes/{id_ingrediente}")
def actualizar_ingrediente(id_ingrediente: str, body: IngredienteActualizar):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    item = service.update_ingredient(id_ingrediente, data)
    if not item:
        raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
    return item


@app.delete("/api/v1/ingredientes/{id_ingrediente}", status_code=204)
def eliminar_ingrediente(id_ingrediente: str):
    if not service.delete_ingredient(id_ingrediente):
        raise HTTPException(status_code=404, detail="Ingrediente no encontrado")


handler = Mangum(app, lifespan="off")
