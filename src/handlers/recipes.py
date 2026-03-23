import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from models.types import RecetaActualizar, RecetaCrear
from services.recipes_service import RecipesService

app = FastAPI(title="Recetas API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
service = RecipesService()


@app.get("/api/v1/recetas")
def listar_recetas(
    id_ingrediente: str | None = Query(None),
    grupo_nutricional: str | None = Query(None),
):
    return service.list_recipes(id_ingrediente, grupo_nutricional)


@app.post("/api/v1/recetas", status_code=201)
def crear_receta(body: RecetaCrear):
    return service.create_recipe(body.model_dump())


@app.get("/api/v1/recetas/{id_receta}")
def obtener_receta(id_receta: str):
    item = service.get_recipe(id_receta)
    if not item:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    return item


@app.put("/api/v1/recetas/{id_receta}")
def actualizar_receta(id_receta: str, body: RecetaActualizar):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    item = service.update_recipe(id_receta, data)
    if not item:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    return item


@app.delete("/api/v1/recetas/{id_receta}", status_code=204)
def eliminar_receta(id_receta: str):
    if not service.delete_recipe(id_receta):
        raise HTTPException(status_code=404, detail="Receta no encontrada")


handler = Mangum(app, lifespan="off")
