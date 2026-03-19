from repositories.ingredients_repository import IngredientsRepository


class IngredientsService:
    def __init__(self):
        self.repo = IngredientsRepository()

    def list_ingredients(self, grupo_nutricional: str = None) -> list[dict]:
        items = self.repo.list_all(grupo_nutricional)
        return [self._format(item) for item in items]

    def get_ingredient(self, id_ingrediente: str) -> dict | None:
        item = self.repo.get_by_id(id_ingrediente)
        return self._format(item) if item else None

    def create_ingredient(self, data: dict) -> dict:
        item = self.repo.create(data)
        return self._format(item)

    def update_ingredient(self, id_ingrediente: str, data: dict) -> dict | None:
        item = self.repo.update(id_ingrediente, data)
        return self._format(item) if item else None

    def delete_ingredient(self, id_ingrediente: str) -> bool:
        return self.repo.delete(id_ingrediente)

    def get_batch(self, ids_ingrediente: list[str]) -> dict[str, dict]:
        items = self.repo.get_batch(ids_ingrediente)
        return {item["id"]: self._format(item) for item in items}

    def _format(self, item: dict) -> dict:
        return {
            "id": item["id"],
            "nombre": item["nombre"],
            "grupo_nutricional": item["grupo_nutricional"],
            "unidad": item["unidad"],
            "creado_en": item.get("creado_en"),
            "actualizado_en": item.get("actualizado_en"),
        }
