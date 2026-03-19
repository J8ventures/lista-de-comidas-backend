from repositories.recipes_repository import RecipesRepository
from services.ingredients_service import IngredientsService


class RecipesService:
    def __init__(self):
        self.repo = RecipesRepository()
        self.ingredients_service = IngredientsService()

    def list_recipes(self, ingredient_id: str = None, nutritional_group: str = None) -> list[dict]:
        if ingredient_id:
            items = self.repo.get_recipes_by_ingredient(ingredient_id)
            recipe_ids = list({item['GSI3SK'].replace('RECIPE#', '') for item in items})
            recipes = [self.repo.get_by_id(rid) for rid in recipe_ids]
            return [self._format(r) for r in recipes if r]
        return [self._format(item) for item in self.repo.list_all()]

    def get_recipe(self, recipe_id: str, populate: bool = True) -> dict | None:
        item = self.repo.get_by_id(recipe_id)
        if not item:
            return None
        recipe = self._format(item)
        if populate:
            recipe['ingredients'] = self._get_populated_ingredients(recipe_id)
        return recipe

    def create_recipe(self, data: dict) -> dict:
        ingredients = data.pop('ingredients', [])
        item = self.repo.create(data)
        recipe_id = item['id']
        if ingredients:
            self.repo.set_ingredients(recipe_id, ingredients)
        recipe = self._format(item)
        recipe['ingredients'] = self._get_populated_ingredients(recipe_id)
        return recipe

    def update_recipe(self, recipe_id: str, data: dict) -> dict | None:
        ingredients = data.pop('ingredients', None)
        item = self.repo.update(recipe_id, data)
        if not item:
            return None
        if ingredients is not None:
            self.repo.set_ingredients(recipe_id, ingredients)
        recipe = self._format(item)
        recipe['ingredients'] = self._get_populated_ingredients(recipe_id)
        return recipe

    def delete_recipe(self, recipe_id: str) -> bool:
        return self.repo.delete(recipe_id)

    def get_recipe_ingredients(self, recipe_id: str) -> list[dict]:
        return self.repo.get_ingredients(recipe_id)

    def _get_populated_ingredients(self, recipe_id: str) -> list[dict]:
        raw = self.repo.get_ingredients(recipe_id)
        ingredient_ids = [r['ingredient_id'] for r in raw]
        alt_ids = [a['ingredient_id'] for r in raw for a in r.get('alternatives', [])]
        all_ids = list(set(ingredient_ids + alt_ids))
        ingredients_map = self.ingredients_service.get_batch(all_ids)

        result = []
        for r in raw:
            entry = {
                'ingredient_id': r['ingredient_id'],
                'ingredient': ingredients_map.get(r['ingredient_id']),
                'role': r['role'],
                'quantity': float(r['quantity']),
                'unit': r['unit'],
                'alternatives': [
                    {
                        'ingredient_id': a['ingredient_id'],
                        'ingredient': ingredients_map.get(a['ingredient_id']),
                        'quantity': float(a['quantity']),
                        'unit': a['unit'],
                    }
                    for a in r.get('alternatives', [])
                ],
            }
            result.append(entry)
        return result

    def _format(self, item: dict) -> dict:
        return {
            'id': item['id'],
            'name': item['name'],
            'description': item.get('description', ''),
            'servings': item.get('servings', 1),
            'prep_time': item.get('prep_time', 0),
            'cook_time': item.get('cook_time', 0),
            'created_at': item.get('created_at'),
            'updated_at': item.get('updated_at'),
        }
