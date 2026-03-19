from repositories.recipes_repository import RecipesRepository
from services.ingredients_service import IngredientsService


class RecipesService:
    def __init__(self):
        self.repo = RecipesRepository()
        self.ingredients_service = IngredientsService()

    def list_recipes(
        self, id_ingrediente: str = None, grupo_nutricional: str = None
    ) -> list[dict]:
        if id_ingrediente:
            items = self.repo.get_recipes_by_ingredient(id_ingrediente)
            ids_receta = list({item["GSI3SK"].replace("RECETA#", "") for item in items})
            recetas = [self.repo.get_by_id(rid) for rid in ids_receta]
            return [self._format(r) for r in recetas if r]
        return [self._format(item) for item in self.repo.list_all()]

    def get_recipe(self, id_receta: str, populate: bool = True) -> dict | None:
        item = self.repo.get_by_id(id_receta)
        if not item:
            return None
        receta = self._format(item)
        if populate:
            receta["ingredientes"] = self._get_populated_ingredients(id_receta)
        return receta

    def create_recipe(self, data: dict) -> dict:
        ingredientes = data.pop("ingredientes", [])
        item = self.repo.create(data)
        id_receta = item["id"]
        if ingredientes:
            self.repo.set_ingredients(id_receta, ingredientes)
        receta = self._format(item)
        receta["ingredientes"] = self._get_populated_ingredients(id_receta)
        return receta

    def update_recipe(self, id_receta: str, data: dict) -> dict | None:
        ingredientes = data.pop("ingredientes", None)
        item = self.repo.update(id_receta, data)
        if not item:
            return None
        if ingredientes is not None:
            self.repo.set_ingredients(id_receta, ingredientes)
        receta = self._format(item)
        receta["ingredientes"] = self._get_populated_ingredients(id_receta)
        return receta

    def delete_recipe(self, id_receta: str) -> bool:
        return self.repo.delete(id_receta)

    def get_recipe_ingredients(self, id_receta: str) -> list[dict]:
        return self.repo.get_ingredients(id_receta)

    def _get_populated_ingredients(self, id_receta: str) -> list[dict]:
        raw = self.repo.get_ingredients(id_receta)
        ids_ingrediente = [r["id_ingrediente"] for r in raw]
        ids_alt = [a["id_ingrediente"] for r in raw for a in r.get("alternativas", [])]
        all_ids = list(set(ids_ingrediente + ids_alt))
        ingredientes_map = self.ingredients_service.get_batch(all_ids)

        result = []
        for r in raw:
            entry = {
                "id_ingrediente": r["id_ingrediente"],
                "ingrediente": ingredientes_map.get(r["id_ingrediente"]),
                "rol": r["rol"],
                "cantidad": float(r["cantidad"]),
                "unidad": r["unidad"],
                "alternativas": [
                    {
                        "id_ingrediente": a["id_ingrediente"],
                        "ingrediente": ingredientes_map.get(a["id_ingrediente"]),
                        "cantidad": float(a["cantidad"]),
                        "unidad": a["unidad"],
                    }
                    for a in r.get("alternativas", [])
                ],
            }
            result.append(entry)
        return result

    def _format(self, item: dict) -> dict:
        return {
            "id": item["id"],
            "nombre": item["nombre"],
            "descripcion": item.get("descripcion", ""),
            "porciones": item.get("porciones", 1),
            "tiempo_preparacion": item.get("tiempo_preparacion", 0),
            "tiempo_coccion": item.get("tiempo_coccion", 0),
            "creado_en": item.get("creado_en"),
            "actualizado_en": item.get("actualizado_en"),
        }
