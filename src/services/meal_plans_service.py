from collections import defaultdict

from repositories.meal_plans_repository import MealPlansRepository
from services.ingredients_service import IngredientsService
from services.recipes_service import RecipesService


class MealPlansService:
    def __init__(self):
        self.repo = MealPlansRepository()
        self.recipes_service = RecipesService()
        self.ingredients_service = IngredientsService()

    def list_meal_plans(self) -> list[dict]:
        return [self._format(item) for item in self.repo.list_all()]

    def get_meal_plan(self, id_plan: str) -> dict | None:
        item = self.repo.get_by_id(id_plan)
        if not item:
            return None
        plan = self._format(item)
        plan["entradas"] = self._format_entries(self.repo.get_entries(id_plan))
        return plan

    def create_meal_plan(self, data: dict) -> dict:
        entradas_data = data.pop("entradas", [])
        item = self.repo.create(data)
        id_plan = item["id"]
        for entrada in entradas_data:
            self.repo.add_entry(id_plan, entrada)
        plan = self._format(item)
        plan["entradas"] = self._format_entries(self.repo.get_entries(id_plan))
        return plan

    def update_meal_plan(self, id_plan: str, data: dict) -> dict | None:
        item = self.repo.update(id_plan, data)
        if not item:
            return None
        plan = self._format(item)
        plan["entradas"] = self._format_entries(self.repo.get_entries(id_plan))
        return plan

    def delete_meal_plan(self, id_plan: str) -> bool:
        return self.repo.delete(id_plan)

    def add_entry(self, id_plan: str, datos_entrada: dict) -> dict | None:
        plan = self.repo.get_by_id(id_plan)
        if not plan:
            return None
        # Validar que ingredientes_seleccionados cubre todos los ingredientes reemplazables
        ingredientes_receta = self.recipes_service.get_recipe_ingredients(
            datos_entrada["id_receta"]
        )
        ids_reemplazables = {
            r["id_ingrediente"]
            for r in ingredientes_receta
            if r["rol"] == "reemplazable"
        }
        seleccionados = set(datos_entrada.get("ingredientes_seleccionados", {}).keys())
        if not ids_reemplazables.issubset(seleccionados):
            faltantes = ids_reemplazables - seleccionados
            raise ValueError(
                f"Faltan ingredientes_seleccionados para ingredientes reemplazables: {faltantes}"
            )
        return self.repo.add_entry(id_plan, datos_entrada)

    def get_meal_list(self, id_plan: str) -> list[dict]:
        entradas = self.repo.get_entries(id_plan)
        entradas_ordenadas = sorted(
            entradas, key=lambda e: (e["fecha"], e["tipo_comida"])
        )
        result = []
        for entrada in entradas_ordenadas:
            receta = self.recipes_service.get_recipe(
                entrada["id_receta"], populate=False
            )
            result.append(
                {
                    "id": entrada["id"],
                    "fecha": entrada["fecha"],
                    "tipo_comida": entrada["tipo_comida"],
                    "receta": receta,
                    "ingredientes_seleccionados": entrada.get(
                        "ingredientes_seleccionados", {}
                    ),
                }
            )
        return result

    def get_grocery_list(self, id_plan: str) -> dict:
        entradas = self.repo.get_entries(id_plan)
        agg_requeridos: dict[str, dict] = defaultdict(
            lambda: {"cantidad": 0.0, "ingrediente": None}
        )
        agg_opcionales: dict[str, dict] = defaultdict(
            lambda: {"cantidad": 0.0, "ingrediente": None}
        )

        all_ids_ingrediente = set()
        entradas_con_ingredientes = []

        for entrada in entradas:
            ingredientes_receta = self.recipes_service.get_recipe_ingredients(
                entrada["id_receta"]
            )
            seleccionados = entrada.get("ingredientes_seleccionados", {})
            entradas_con_ingredientes.append(
                (entrada, ingredientes_receta, seleccionados)
            )
            for ri in ingredientes_receta:
                all_ids_ingrediente.add(ri["id_ingrediente"])
                for alt in ri.get("alternativas", []):
                    all_ids_ingrediente.add(alt["id_ingrediente"])
                for id_elegido in seleccionados.values():
                    all_ids_ingrediente.add(id_elegido)

        ingredientes_map = self.ingredients_service.get_batch(list(all_ids_ingrediente))

        for _entrada, ingredientes_receta, seleccionados in entradas_con_ingredientes:
            for ri in ingredientes_receta:
                rol = ri["rol"]
                cantidad = float(ri["cantidad"])
                unidad = ri["unidad"]

                if rol == "requerido":
                    iid = ri["id_ingrediente"]
                    agg_requeridos[iid]["cantidad"] += cantidad
                    agg_requeridos[iid]["unidad"] = unidad
                    agg_requeridos[iid]["ingrediente"] = ingredientes_map.get(iid)

                elif rol == "reemplazable":
                    id_orig = ri["id_ingrediente"]
                    id_elegido = seleccionados.get(id_orig, id_orig)
                    cantidad_elegida = cantidad
                    unidad_elegida = unidad
                    for alt in ri.get("alternativas", []):
                        if alt["id_ingrediente"] == id_elegido:
                            cantidad_elegida = float(alt["cantidad"])
                            unidad_elegida = alt["unidad"]
                            break
                    agg_requeridos[id_elegido]["cantidad"] += cantidad_elegida
                    agg_requeridos[id_elegido]["unidad"] = unidad_elegida
                    agg_requeridos[id_elegido]["ingrediente"] = ingredientes_map.get(
                        id_elegido
                    )

                elif rol == "opcional":
                    iid = ri["id_ingrediente"]
                    agg_opcionales[iid]["cantidad"] += cantidad
                    agg_opcionales[iid]["unidad"] = unidad
                    agg_opcionales[iid]["ingrediente"] = ingredientes_map.get(iid)

        def agg_a_lista(agg: dict) -> list[dict]:
            return [
                {
                    "ingrediente": v["ingrediente"],
                    "cantidad": v["cantidad"],
                    "unidad": v["unidad"],
                }
                for v in agg.values()
            ]

        return {
            "requeridos": agg_a_lista(agg_requeridos),
            "opcionales": agg_a_lista(agg_opcionales),
        }

    def _format(self, item: dict) -> dict:
        return {
            "id": item["id"],
            "nombre": item["nombre"],
            "tipo": item["tipo"],
            "fecha_inicio": item["fecha_inicio"],
            "fecha_fin": item["fecha_fin"],
            "creado_en": item.get("creado_en"),
            "actualizado_en": item.get("actualizado_en"),
        }

    def _format_entries(self, entradas: list[dict]) -> list[dict]:
        return [
            {
                "id": e["id"],
                "fecha": e["fecha"],
                "tipo_comida": e["tipo_comida"],
                "id_receta": e["id_receta"],
                "ingredientes_seleccionados": e.get("ingredientes_seleccionados", {}),
            }
            for e in entradas
        ]
