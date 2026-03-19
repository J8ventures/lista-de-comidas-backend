from unittest.mock import MagicMock, patch
import pytest

from services.recipes_service import RecipesService


RAW_RECIPE = {
    'id': 'rec-1',
    'nombre': 'Pollo asado',
    'descripcion': 'Clásico pollo asado',
    'porciones': 4,
    'tiempo_preparacion': 15,
    'tiempo_coccion': 60,
    'creado_en': '2024-01-01T00:00:00',
    'actualizado_en': '2024-01-01T00:00:00',
}

FORMATTED_RECIPE = {
    'id': 'rec-1',
    'nombre': 'Pollo asado',
    'descripcion': 'Clásico pollo asado',
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

RAW_RECIPE_ING = {
    'id_ingrediente': 'ing-1',
    'rol': 'requerido',
    'cantidad': '500',
    'unidad': 'g',
    'alternativas': [],
}


@pytest.fixture
def service():
    with patch('services.recipes_service.RecipesRepository') as MockRepo, \
         patch('services.recipes_service.IngredientsService') as MockIngSvc:
        svc = RecipesService()
        svc.repo = MockRepo()
        svc.ingredients_service = MockIngSvc()
        yield svc


def test_list_recipes_all(service):
    service.repo.list_all.return_value = [RAW_RECIPE]
    result = service.list_recipes()
    assert len(result) == 1
    assert result[0]['nombre'] == 'Pollo asado'


def test_list_recipes_by_ingredient(service):
    service.repo.get_recipes_by_ingredient.return_value = [
        {'GSI3SK': 'RECETA#rec-1'}
    ]
    service.repo.get_by_id.return_value = RAW_RECIPE
    result = service.list_recipes(id_ingrediente='ing-1')
    service.repo.get_recipes_by_ingredient.assert_called_once_with('ing-1')
    assert len(result) == 1


def test_list_recipes_by_ingredient_deduplicates(service):
    # Two GSI3 items pointing to same recipe → only fetched once
    service.repo.get_recipes_by_ingredient.return_value = [
        {'GSI3SK': 'RECETA#rec-1'},
        {'GSI3SK': 'RECETA#rec-1'},
    ]
    service.repo.get_by_id.return_value = RAW_RECIPE
    result = service.list_recipes(id_ingrediente='ing-1')
    assert service.repo.get_by_id.call_count == 1
    assert len(result) == 1


def test_get_recipe_found_with_population(service):
    service.repo.get_by_id.return_value = RAW_RECIPE
    service.repo.get_ingredients.return_value = [RAW_RECIPE_ING]
    service.ingredients_service.get_batch.return_value = {'ing-1': RAW_ING}
    result = service.get_recipe('rec-1')
    assert result['nombre'] == 'Pollo asado'
    assert len(result['ingredientes']) == 1
    assert result['ingredientes'][0]['id_ingrediente'] == 'ing-1'
    assert result['ingredientes'][0]['cantidad'] == 500.0


def test_get_recipe_found_without_population(service):
    service.repo.get_by_id.return_value = RAW_RECIPE
    result = service.get_recipe('rec-1', populate=False)
    assert result['nombre'] == 'Pollo asado'
    assert 'ingredientes' not in result
    service.repo.get_ingredients.assert_not_called()


def test_get_recipe_not_found(service):
    service.repo.get_by_id.return_value = None
    result = service.get_recipe('nonexistent')
    assert result is None


def test_create_recipe_without_ingredients(service):
    data = {'nombre': 'Pollo asado', 'descripcion': '', 'porciones': 1,
            'tiempo_preparacion': 0, 'tiempo_coccion': 0, 'ingredientes': []}
    service.repo.create.return_value = RAW_RECIPE
    service.repo.get_ingredients.return_value = []
    service.ingredients_service.get_batch.return_value = {}
    result = service.create_recipe(data)
    assert result['nombre'] == 'Pollo asado'
    assert result['ingredientes'] == []
    service.repo.set_ingredients.assert_not_called()


def test_create_recipe_with_ingredients(service):
    ing_data = [{'id_ingrediente': 'ing-1', 'rol': 'requerido', 'cantidad': 500, 'unidad': 'g', 'alternativas': []}]
    data = {'nombre': 'Pollo asado', 'ingredientes': ing_data}
    service.repo.create.return_value = RAW_RECIPE
    service.repo.get_ingredients.return_value = [RAW_RECIPE_ING]
    service.ingredients_service.get_batch.return_value = {'ing-1': RAW_ING}
    service.create_recipe(data)
    service.repo.set_ingredients.assert_called_once_with('rec-1', ing_data)


def test_update_recipe_found(service):
    service.repo.update.return_value = {**RAW_RECIPE, 'nombre': 'Pollo al horno'}
    service.repo.get_ingredients.return_value = []
    service.ingredients_service.get_batch.return_value = {}
    result = service.update_recipe('rec-1', {'nombre': 'Pollo al horno'})
    assert result['nombre'] == 'Pollo al horno'
    service.repo.set_ingredients.assert_not_called()


def test_update_recipe_with_new_ingredients(service):
    new_ings = [{'id_ingrediente': 'ing-2', 'rol': 'requerido', 'cantidad': 100, 'unidad': 'g', 'alternativas': []}]
    service.repo.update.return_value = RAW_RECIPE
    service.repo.get_ingredients.return_value = []
    service.ingredients_service.get_batch.return_value = {}
    service.update_recipe('rec-1', {'ingredientes': new_ings})
    service.repo.set_ingredients.assert_called_once_with('rec-1', new_ings)


def test_update_recipe_not_found(service):
    service.repo.update.return_value = None
    result = service.update_recipe('nonexistent', {'nombre': 'X'})
    assert result is None


def test_delete_recipe(service):
    service.repo.delete.return_value = True
    assert service.delete_recipe('rec-1') is True


def test_populated_ingredient_with_alternatives(service):
    raw_ing_with_alt = {
        'id_ingrediente': 'ing-1',
        'rol': 'reemplazable',
        'cantidad': '500',
        'unidad': 'g',
        'alternativas': [{'id_ingrediente': 'ing-2', 'cantidad': '400', 'unidad': 'g'}],
    }
    alt_ing = {**RAW_ING, 'id': 'ing-2', 'nombre': 'Pechuga'}
    service.repo.get_by_id.return_value = RAW_RECIPE
    service.repo.get_ingredients.return_value = [raw_ing_with_alt]
    service.ingredients_service.get_batch.return_value = {
        'ing-1': RAW_ING,
        'ing-2': alt_ing,
    }
    result = service.get_recipe('rec-1')
    ing = result['ingredientes'][0]
    assert ing['rol'] == 'reemplazable'
    assert len(ing['alternativas']) == 1
    assert ing['alternativas'][0]['id_ingrediente'] == 'ing-2'
    assert ing['alternativas'][0]['cantidad'] == 400.0
