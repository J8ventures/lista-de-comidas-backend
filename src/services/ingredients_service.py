from repositories.ingredients_repository import IngredientsRepository


class IngredientsService:
    def __init__(self):
        self.repo = IngredientsRepository()

    def list_ingredients(self, nutritional_group: str = None) -> list[dict]:
        items = self.repo.list_all(nutritional_group)
        return [self._format(item) for item in items]

    def get_ingredient(self, ingredient_id: str) -> dict | None:
        item = self.repo.get_by_id(ingredient_id)
        return self._format(item) if item else None

    def create_ingredient(self, data: dict) -> dict:
        item = self.repo.create(data)
        return self._format(item)

    def update_ingredient(self, ingredient_id: str, data: dict) -> dict | None:
        item = self.repo.update(ingredient_id, data)
        return self._format(item) if item else None

    def delete_ingredient(self, ingredient_id: str) -> bool:
        return self.repo.delete(ingredient_id)

    def get_batch(self, ingredient_ids: list[str]) -> dict[str, dict]:
        items = self.repo.get_batch(ingredient_ids)
        return {item['id']: self._format(item) for item in items}

    def _format(self, item: dict) -> dict:
        return {
            'id': item['id'],
            'name': item['name'],
            'nutritional_group': item['nutritional_group'],
            'unit': item['unit'],
            'created_at': item.get('created_at'),
            'updated_at': item.get('updated_at'),
        }
