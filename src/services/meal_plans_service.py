from collections import defaultdict
from repositories.meal_plans_repository import MealPlansRepository
from services.recipes_service import RecipesService
from services.ingredients_service import IngredientsService


class MealPlansService:
    def __init__(self):
        self.repo = MealPlansRepository()
        self.recipes_service = RecipesService()
        self.ingredients_service = IngredientsService()

    def list_meal_plans(self) -> list[dict]:
        return [self._format(item) for item in self.repo.list_all()]

    def get_meal_plan(self, plan_id: str) -> dict | None:
        item = self.repo.get_by_id(plan_id)
        if not item:
            return None
        plan = self._format(item)
        plan['entries'] = self._format_entries(self.repo.get_entries(plan_id))
        return plan

    def create_meal_plan(self, data: dict) -> dict:
        entries_data = data.pop('entries', [])
        item = self.repo.create(data)
        plan_id = item['id']
        for entry in entries_data:
            self.repo.add_entry(plan_id, entry)
        plan = self._format(item)
        plan['entries'] = self._format_entries(self.repo.get_entries(plan_id))
        return plan

    def update_meal_plan(self, plan_id: str, data: dict) -> dict | None:
        item = self.repo.update(plan_id, data)
        if not item:
            return None
        plan = self._format(item)
        plan['entries'] = self._format_entries(self.repo.get_entries(plan_id))
        return plan

    def delete_meal_plan(self, plan_id: str) -> bool:
        return self.repo.delete(plan_id)

    def add_entry(self, plan_id: str, entry_data: dict) -> dict | None:
        plan = self.repo.get_by_id(plan_id)
        if not plan:
            return None
        # Validate selected_ingredients covers all replaceable ingredients
        recipe_ingredients = self.recipes_service.get_recipe_ingredients(entry_data['recipe_id'])
        replaceable_ids = {r['ingredient_id'] for r in recipe_ingredients if r['role'] == 'replaceable'}
        selected = set(entry_data.get('selected_ingredients', {}).keys())
        if not replaceable_ids.issubset(selected):
            missing = replaceable_ids - selected
            raise ValueError(f"Missing selected_ingredients for replaceable ingredients: {missing}")
        return self.repo.add_entry(plan_id, entry_data)

    def get_meal_list(self, plan_id: str) -> list[dict]:
        entries = self.repo.get_entries(plan_id)
        sorted_entries = sorted(entries, key=lambda e: (e['date'], e['meal_type']))
        result = []
        for entry in sorted_entries:
            recipe = self.recipes_service.get_recipe(entry['recipe_id'], populate=False)
            result.append({
                'id': entry['id'],
                'date': entry['date'],
                'meal_type': entry['meal_type'],
                'recipe': recipe,
                'selected_ingredients': entry.get('selected_ingredients', {}),
            })
        return result

    def get_grocery_list(self, plan_id: str) -> dict:
        entries = self.repo.get_entries(plan_id)
        required_agg: dict[str, dict] = defaultdict(lambda: {'quantity': 0.0, 'ingredient': None})
        optional_agg: dict[str, dict] = defaultdict(lambda: {'quantity': 0.0, 'ingredient': None})

        all_ingredient_ids = set()
        entries_with_ingredients = []

        for entry in entries:
            recipe_ingredients = self.recipes_service.get_recipe_ingredients(entry['recipe_id'])
            selected = entry.get('selected_ingredients', {})
            entries_with_ingredients.append((entry, recipe_ingredients, selected))
            for ri in recipe_ingredients:
                all_ingredient_ids.add(ri['ingredient_id'])
                for alt in ri.get('alternatives', []):
                    all_ingredient_ids.add(alt['ingredient_id'])
                for chosen_id in selected.values():
                    all_ingredient_ids.add(chosen_id)

        ingredients_map = self.ingredients_service.get_batch(list(all_ingredient_ids))

        for entry, recipe_ingredients, selected in entries_with_ingredients:
            for ri in recipe_ingredients:
                role = ri['role']
                qty = float(ri['quantity'])
                unit = ri['unit']

                if role == 'required':
                    iid = ri['ingredient_id']
                    required_agg[iid]['quantity'] += qty
                    required_agg[iid]['unit'] = unit
                    required_agg[iid]['ingredient'] = ingredients_map.get(iid)

                elif role == 'replaceable':
                    orig_id = ri['ingredient_id']
                    chosen_id = selected.get(orig_id, orig_id)
                    # Find quantity from alternative if chosen is an alternative
                    chosen_qty = qty
                    chosen_unit = unit
                    for alt in ri.get('alternatives', []):
                        if alt['ingredient_id'] == chosen_id:
                            chosen_qty = float(alt['quantity'])
                            chosen_unit = alt['unit']
                            break
                    required_agg[chosen_id]['quantity'] += chosen_qty
                    required_agg[chosen_id]['unit'] = chosen_unit
                    required_agg[chosen_id]['ingredient'] = ingredients_map.get(chosen_id)

                elif role == 'optional':
                    iid = ri['ingredient_id']
                    optional_agg[iid]['quantity'] += qty
                    optional_agg[iid]['unit'] = unit
                    optional_agg[iid]['ingredient'] = ingredients_map.get(iid)

        def agg_to_list(agg: dict) -> list[dict]:
            return [
                {'ingredient': v['ingredient'], 'quantity': v['quantity'], 'unit': v['unit']}
                for v in agg.values()
            ]

        return {
            'required': agg_to_list(required_agg),
            'optional': agg_to_list(optional_agg),
        }

    def _format(self, item: dict) -> dict:
        return {
            'id': item['id'],
            'name': item['name'],
            'type': item['type'],
            'start_date': item['start_date'],
            'end_date': item['end_date'],
            'created_at': item.get('created_at'),
            'updated_at': item.get('updated_at'),
        }

    def _format_entries(self, entries: list[dict]) -> list[dict]:
        return [
            {
                'id': e['id'],
                'date': e['date'],
                'meal_type': e['meal_type'],
                'recipe_id': e['recipe_id'],
                'selected_ingredients': e.get('selected_ingredients', {}),
            }
            for e in entries
        ]
