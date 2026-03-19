from unittest.mock import MagicMock, patch
import pytest

from services.meal_plans_service import MealPlansService


RAW_PLAN = {
    'id': 'plan-1',
    'nombre': 'Plan semana 1',
    'tipo': 'semanal',
    'fecha_inicio': '2024-01-01',
    'fecha_fin': '2024-01-07',
    'creado_en': '2024-01-01T00:00:00',
    'actualizado_en': '2024-01-01T00:00:00',
}

RAW_ENTRY = {
    'id': 'entry-1',
    'fecha': '2024-01-01',
    'tipo_comida': 'almuerzo',
    'id_receta': 'rec-1',
    'ingredientes_seleccionados': {},
}

RAW_RECIPE = {
    'id': 'rec-1',
    'nombre': 'Pollo asado',
    'descripcion': '',
    'porciones': 4,
    'tiempo_preparacion': 15,
    'tiempo_coccion': 60,
    'creado_en': '2024-01-01T00:00:00',
    'actualizado_en': '2024-01-01T00:00:00',
}

RAW_ING = {
    'id': 'ing-1',
    'nombre': 'Pollo',
    'grupo_nutricional': 'PROTEINAS',
    'unidad': 'g',
    'creado_en': '2024-01-01T00:00:00',
    'actualizado_en': '2024-01-01T00:00:00',
}


@pytest.fixture
def service():
    with patch('services.meal_plans_service.MealPlansRepository') as MockRepo, \
         patch('services.meal_plans_service.RecipesService') as MockRecSvc, \
         patch('services.meal_plans_service.IngredientsService') as MockIngSvc:
        svc = MealPlansService()
        svc.repo = MockRepo()
        svc.recipes_service = MockRecSvc()
        svc.ingredients_service = MockIngSvc()
        yield svc


def test_list_meal_plans(service):
    service.repo.list_all.return_value = [RAW_PLAN]
    result = service.list_meal_plans()
    assert len(result) == 1
    assert result[0]['nombre'] == 'Plan semana 1'


def test_list_meal_plans_empty(service):
    service.repo.list_all.return_value = []
    assert service.list_meal_plans() == []


def test_get_meal_plan_found(service):
    service.repo.get_by_id.return_value = RAW_PLAN
    service.repo.get_entries.return_value = [RAW_ENTRY]
    result = service.get_meal_plan('plan-1')
    assert result['nombre'] == 'Plan semana 1'
    assert len(result['entradas']) == 1
    assert result['entradas'][0]['id'] == 'entry-1'


def test_get_meal_plan_not_found(service):
    service.repo.get_by_id.return_value = None
    result = service.get_meal_plan('nonexistent')
    assert result is None


def test_create_meal_plan_without_entries(service):
    data = {**{k: v for k, v in RAW_PLAN.items() if k in ('nombre', 'tipo', 'fecha_inicio', 'fecha_fin')},
            'entradas': []}
    service.repo.create.return_value = RAW_PLAN
    service.repo.get_entries.return_value = []
    result = service.create_meal_plan(data)
    assert result['nombre'] == 'Plan semana 1'
    assert result['entradas'] == []
    service.repo.add_entry.assert_not_called()


def test_create_meal_plan_with_entries(service):
    entrada = {'fecha': '2024-01-01', 'tipo_comida': 'almuerzo', 'id_receta': 'rec-1',
               'ingredientes_seleccionados': {}}
    data = {'nombre': 'Plan', 'tipo': 'semanal', 'fecha_inicio': '2024-01-01',
            'fecha_fin': '2024-01-07', 'entradas': [entrada]}
    service.repo.create.return_value = RAW_PLAN
    service.repo.get_entries.return_value = [RAW_ENTRY]
    service.create_meal_plan(data)
    service.repo.add_entry.assert_called_once_with('plan-1', entrada)


def test_update_meal_plan_found(service):
    service.repo.update.return_value = {**RAW_PLAN, 'nombre': 'Plan actualizado'}
    service.repo.get_entries.return_value = []
    result = service.update_meal_plan('plan-1', {'nombre': 'Plan actualizado'})
    assert result['nombre'] == 'Plan actualizado'


def test_update_meal_plan_not_found(service):
    service.repo.update.return_value = None
    result = service.update_meal_plan('nonexistent', {'nombre': 'X'})
    assert result is None


def test_delete_meal_plan(service):
    service.repo.delete.return_value = True
    assert service.delete_meal_plan('plan-1') is True


def test_add_entry_success_no_replaceable(service):
    service.repo.get_by_id.return_value = RAW_PLAN
    service.recipes_service.get_recipe_ingredients.return_value = [
        {'id_ingrediente': 'ing-1', 'rol': 'requerido'}
    ]
    service.repo.add_entry.return_value = RAW_ENTRY
    datos = {'fecha': '2024-01-01', 'tipo_comida': 'almuerzo', 'id_receta': 'rec-1',
             'ingredientes_seleccionados': {}}
    result = service.add_entry('plan-1', datos)
    assert result == RAW_ENTRY


def test_add_entry_success_replaceable_covered(service):
    service.repo.get_by_id.return_value = RAW_PLAN
    service.recipes_service.get_recipe_ingredients.return_value = [
        {'id_ingrediente': 'ing-1', 'rol': 'reemplazable'}
    ]
    service.repo.add_entry.return_value = RAW_ENTRY
    datos = {'fecha': '2024-01-01', 'tipo_comida': 'almuerzo', 'id_receta': 'rec-1',
             'ingredientes_seleccionados': {'ing-1': 'ing-2'}}
    result = service.add_entry('plan-1', datos)
    assert result == RAW_ENTRY


def test_add_entry_fails_replaceable_not_covered(service):
    service.repo.get_by_id.return_value = RAW_PLAN
    service.recipes_service.get_recipe_ingredients.return_value = [
        {'id_ingrediente': 'ing-1', 'rol': 'reemplazable'},
        {'id_ingrediente': 'ing-2', 'rol': 'reemplazable'},
    ]
    datos = {'fecha': '2024-01-01', 'tipo_comida': 'almuerzo', 'id_receta': 'rec-1',
             'ingredientes_seleccionados': {'ing-1': 'ing-3'}}  # ing-2 missing
    with pytest.raises(ValueError, match='ingredientes_seleccionados'):
        service.add_entry('plan-1', datos)


def test_add_entry_plan_not_found(service):
    service.repo.get_by_id.return_value = None
    datos = {'fecha': '2024-01-01', 'tipo_comida': 'almuerzo', 'id_receta': 'rec-1',
             'ingredientes_seleccionados': {}}
    result = service.add_entry('nonexistent', datos)
    assert result is None


def test_get_meal_list_sorted(service):
    entries = [
        {**RAW_ENTRY, 'id': 'e2', 'fecha': '2024-01-02', 'tipo_comida': 'desayuno'},
        {**RAW_ENTRY, 'id': 'e1', 'fecha': '2024-01-01', 'tipo_comida': 'cena'},
    ]
    service.repo.get_entries.return_value = entries
    service.recipes_service.get_recipe.return_value = RAW_RECIPE
    result = service.get_meal_list('plan-1')
    assert result[0]['fecha'] == '2024-01-01'
    assert result[1]['fecha'] == '2024-01-02'


def test_get_meal_list_includes_recipe(service):
    service.repo.get_entries.return_value = [RAW_ENTRY]
    service.recipes_service.get_recipe.return_value = RAW_RECIPE
    result = service.get_meal_list('plan-1')
    assert result[0]['receta']['nombre'] == 'Pollo asado'
    service.recipes_service.get_recipe.assert_called_with('rec-1', populate=False)


def test_get_grocery_list_required_ingredient(service):
    entry = {**RAW_ENTRY, 'ingredientes_seleccionados': {}}
    service.repo.get_entries.return_value = [entry]
    service.recipes_service.get_recipe_ingredients.return_value = [
        {'id_ingrediente': 'ing-1', 'rol': 'requerido', 'cantidad': '200', 'unidad': 'g', 'alternativas': []}
    ]
    service.ingredients_service.get_batch.return_value = {'ing-1': RAW_ING}
    result = service.get_grocery_list('plan-1')
    assert len(result['requeridos']) == 1
    assert result['requeridos'][0]['cantidad'] == 200.0
    assert result['requeridos'][0]['ingrediente']['nombre'] == 'Pollo'
    assert result['opcionales'] == []


def test_get_grocery_list_optional_ingredient(service):
    entry = {**RAW_ENTRY, 'ingredientes_seleccionados': {}}
    service.repo.get_entries.return_value = [entry]
    service.recipes_service.get_recipe_ingredients.return_value = [
        {'id_ingrediente': 'ing-1', 'rol': 'opcional', 'cantidad': '50', 'unidad': 'g', 'alternativas': []}
    ]
    service.ingredients_service.get_batch.return_value = {'ing-1': RAW_ING}
    result = service.get_grocery_list('plan-1')
    assert result['requeridos'] == []
    assert len(result['opcionales']) == 1
    assert result['opcionales'][0]['cantidad'] == 50.0


def test_get_grocery_list_replaceable_uses_selection(service):
    ing_alt = {**RAW_ING, 'id': 'ing-2', 'nombre': 'Pechuga'}
    entry = {**RAW_ENTRY, 'ingredientes_seleccionados': {'ing-1': 'ing-2'}}
    service.repo.get_entries.return_value = [entry]
    service.recipes_service.get_recipe_ingredients.return_value = [
        {
            'id_ingrediente': 'ing-1',
            'rol': 'reemplazable',
            'cantidad': '500',
            'unidad': 'g',
            'alternativas': [{'id_ingrediente': 'ing-2', 'cantidad': '400', 'unidad': 'g'}],
        }
    ]
    service.ingredients_service.get_batch.return_value = {'ing-1': RAW_ING, 'ing-2': ing_alt}
    result = service.get_grocery_list('plan-1')
    # Should use the alternative (ing-2) with its quantity (400g), not the original (ing-1, 500g)
    assert len(result['requeridos']) == 1
    assert result['requeridos'][0]['ingrediente']['nombre'] == 'Pechuga'
    assert result['requeridos'][0]['cantidad'] == 400.0


def test_get_grocery_list_aggregates_quantities(service):
    entries = [
        {**RAW_ENTRY, 'id': 'e1', 'ingredientes_seleccionados': {}},
        {**RAW_ENTRY, 'id': 'e2', 'ingredientes_seleccionados': {}},
    ]
    service.repo.get_entries.return_value = entries
    service.recipes_service.get_recipe_ingredients.return_value = [
        {'id_ingrediente': 'ing-1', 'rol': 'requerido', 'cantidad': '200', 'unidad': 'g', 'alternativas': []}
    ]
    service.ingredients_service.get_batch.return_value = {'ing-1': RAW_ING}
    result = service.get_grocery_list('plan-1')
    assert result['requeridos'][0]['cantidad'] == 400.0  # 200 * 2 entries


def test_get_grocery_list_empty_plan(service):
    service.repo.get_entries.return_value = []
    service.ingredients_service.get_batch.return_value = {}
    result = service.get_grocery_list('plan-1')
    assert result == {'requeridos': [], 'opcionales': []}
