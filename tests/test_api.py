"""
Integration tests for the FastAPI HTTP layer.
Services are mocked — these tests verify routing, request parsing, and response codes.
"""
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

import src.handlers.ingredients as ing_handler
import src.handlers.recipes as rec_handler
import src.handlers.meal_plans as mp_handler
import local_server


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_ing(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(ing_handler, 'service', mock)
    return mock


@pytest.fixture
def mock_rec(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(rec_handler, 'service', mock)
    return mock


@pytest.fixture
def mock_mp(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(mp_handler, 'service', mock)
    return mock


@pytest.fixture
def client():
    return TestClient(local_server.app)


INGREDIENT = {
    'id': 'ing-1',
    'nombre': 'Pollo',
    'grupo_nutricional': 'PROTEINAS',
    'unidad': 'g',
    'creado_en': '2024-01-01T00:00:00',
    'actualizado_en': '2024-01-01T00:00:00',
}

RECIPE = {
    'id': 'rec-1',
    'nombre': 'Pollo asado',
    'descripcion': '',
    'porciones': 4,
    'tiempo_preparacion': 15,
    'tiempo_coccion': 60,
    'ingredientes': [],
    'creado_en': '2024-01-01T00:00:00',
    'actualizado_en': '2024-01-01T00:00:00',
}

PLAN = {
    'id': 'plan-1',
    'nombre': 'Plan semana 1',
    'tipo': 'semanal',
    'fecha_inicio': '2024-01-01',
    'fecha_fin': '2024-01-07',
    'entradas': [],
    'creado_en': '2024-01-01T00:00:00',
    'actualizado_en': '2024-01-01T00:00:00',
}


# ---------------------------------------------------------------------------
# Ingredients
# ---------------------------------------------------------------------------

class TestIngredients:
    def test_list_returns_200(self, client, mock_ing):
        mock_ing.list_ingredients.return_value = [INGREDIENT]
        r = client.get('/api/v1/ingredientes')
        assert r.status_code == 200
        assert r.json()[0]['nombre'] == 'Pollo'

    def test_list_filters_by_group(self, client, mock_ing):
        mock_ing.list_ingredients.return_value = []
        client.get('/api/v1/ingredientes?grupo_nutricional=PROTEINAS')
        mock_ing.list_ingredients.assert_called_with('PROTEINAS')

    def test_create_returns_201(self, client, mock_ing):
        mock_ing.create_ingredient.return_value = INGREDIENT
        r = client.post('/api/v1/ingredientes', json={
            'nombre': 'Pollo',
            'grupo_nutricional': 'PROTEINAS',
            'unidad': 'g',
        })
        assert r.status_code == 201

    def test_create_invalid_group_returns_422(self, client, mock_ing):
        r = client.post('/api/v1/ingredientes', json={
            'nombre': 'X',
            'grupo_nutricional': 'INVALID',
            'unidad': 'g',
        })
        assert r.status_code == 422

    def test_get_existing_returns_200(self, client, mock_ing):
        mock_ing.get_ingredient.return_value = INGREDIENT
        r = client.get('/api/v1/ingredientes/ing-1')
        assert r.status_code == 200
        assert r.json()['id'] == 'ing-1'

    def test_get_missing_returns_404(self, client, mock_ing):
        mock_ing.get_ingredient.return_value = None
        r = client.get('/api/v1/ingredientes/nonexistent')
        assert r.status_code == 404

    def test_update_existing_returns_200(self, client, mock_ing):
        mock_ing.update_ingredient.return_value = {**INGREDIENT, 'nombre': 'Pechuga'}
        r = client.put('/api/v1/ingredientes/ing-1', json={'nombre': 'Pechuga'})
        assert r.status_code == 200
        assert r.json()['nombre'] == 'Pechuga'

    def test_update_missing_returns_404(self, client, mock_ing):
        mock_ing.update_ingredient.return_value = None
        r = client.put('/api/v1/ingredientes/nonexistent', json={'nombre': 'X'})
        assert r.status_code == 404

    def test_delete_existing_returns_204(self, client, mock_ing):
        mock_ing.delete_ingredient.return_value = True
        r = client.delete('/api/v1/ingredientes/ing-1')
        assert r.status_code == 204

    def test_delete_missing_returns_404(self, client, mock_ing):
        mock_ing.delete_ingredient.return_value = False
        r = client.delete('/api/v1/ingredientes/nonexistent')
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------

class TestRecipes:
    def test_list_returns_200(self, client, mock_rec):
        mock_rec.list_recipes.return_value = [RECIPE]
        r = client.get('/api/v1/recetas')
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_list_with_filters(self, client, mock_rec):
        mock_rec.list_recipes.return_value = []
        client.get('/api/v1/recetas?id_ingrediente=ing-1&grupo_nutricional=PROTEINAS')
        mock_rec.list_recipes.assert_called_with('ing-1', 'PROTEINAS')

    def test_create_returns_201(self, client, mock_rec):
        mock_rec.create_recipe.return_value = RECIPE
        r = client.post('/api/v1/recetas', json={'nombre': 'Pollo asado'})
        assert r.status_code == 201

    def test_get_existing_returns_200(self, client, mock_rec):
        mock_rec.get_recipe.return_value = RECIPE
        r = client.get('/api/v1/recetas/rec-1')
        assert r.status_code == 200

    def test_get_missing_returns_404(self, client, mock_rec):
        mock_rec.get_recipe.return_value = None
        r = client.get('/api/v1/recetas/nonexistent')
        assert r.status_code == 404

    def test_update_existing_returns_200(self, client, mock_rec):
        mock_rec.update_recipe.return_value = RECIPE
        r = client.put('/api/v1/recetas/rec-1', json={'nombre': 'Pollo al horno'})
        assert r.status_code == 200

    def test_update_missing_returns_404(self, client, mock_rec):
        mock_rec.update_recipe.return_value = None
        r = client.put('/api/v1/recetas/nonexistent', json={'nombre': 'X'})
        assert r.status_code == 404

    def test_delete_existing_returns_204(self, client, mock_rec):
        mock_rec.delete_recipe.return_value = True
        r = client.delete('/api/v1/recetas/rec-1')
        assert r.status_code == 204

    def test_delete_missing_returns_404(self, client, mock_rec):
        mock_rec.delete_recipe.return_value = False
        r = client.delete('/api/v1/recetas/nonexistent')
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Meal Plans
# ---------------------------------------------------------------------------

class TestMealPlans:
    def test_list_returns_200(self, client, mock_mp):
        mock_mp.list_meal_plans.return_value = [PLAN]
        r = client.get('/api/v1/planes-comida')
        assert r.status_code == 200

    def test_create_returns_201(self, client, mock_mp):
        mock_mp.create_meal_plan.return_value = PLAN
        r = client.post('/api/v1/planes-comida', json={
            'nombre': 'Plan semana 1',
            'tipo': 'semanal',
            'fecha_inicio': '2024-01-01',
            'fecha_fin': '2024-01-07',
        })
        assert r.status_code == 201

    def test_create_invalid_type_returns_422(self, client, mock_mp):
        r = client.post('/api/v1/planes-comida', json={
            'nombre': 'Plan',
            'tipo': 'mensual',  # invalid
            'fecha_inicio': '2024-01-01',
            'fecha_fin': '2024-01-31',
        })
        assert r.status_code == 422

    def test_get_existing_returns_200(self, client, mock_mp):
        mock_mp.get_meal_plan.return_value = PLAN
        r = client.get('/api/v1/planes-comida/plan-1')
        assert r.status_code == 200

    def test_get_missing_returns_404(self, client, mock_mp):
        mock_mp.get_meal_plan.return_value = None
        r = client.get('/api/v1/planes-comida/nonexistent')
        assert r.status_code == 404

    def test_update_existing_returns_200(self, client, mock_mp):
        mock_mp.update_meal_plan.return_value = PLAN
        r = client.put('/api/v1/planes-comida/plan-1', json={'nombre': 'Actualizado'})
        assert r.status_code == 200

    def test_update_missing_returns_404(self, client, mock_mp):
        mock_mp.update_meal_plan.return_value = None
        r = client.put('/api/v1/planes-comida/nonexistent', json={'nombre': 'X'})
        assert r.status_code == 404

    def test_delete_existing_returns_204(self, client, mock_mp):
        mock_mp.delete_meal_plan.return_value = True
        r = client.delete('/api/v1/planes-comida/plan-1')
        assert r.status_code == 204

    def test_delete_missing_returns_404(self, client, mock_mp):
        mock_mp.delete_meal_plan.return_value = False
        r = client.delete('/api/v1/planes-comida/nonexistent')
        assert r.status_code == 404

    def test_add_entry_returns_201(self, client, mock_mp):
        entry = {'id': 'e-1', 'fecha': '2024-01-01', 'tipo_comida': 'almuerzo',
                 'id_receta': 'rec-1', 'ingredientes_seleccionados': {}}
        mock_mp.add_entry.return_value = entry
        r = client.post('/api/v1/planes-comida/plan-1/entradas', json={
            'fecha': '2024-01-01',
            'tipo_comida': 'almuerzo',
            'id_receta': 'rec-1',
        })
        assert r.status_code == 201

    def test_add_entry_plan_not_found_returns_404(self, client, mock_mp):
        mock_mp.add_entry.return_value = None
        r = client.post('/api/v1/planes-comida/nonexistent/entradas', json={
            'fecha': '2024-01-01',
            'tipo_comida': 'almuerzo',
            'id_receta': 'rec-1',
        })
        assert r.status_code == 404

    def test_add_entry_missing_replaceable_returns_422(self, client, mock_mp):
        mock_mp.add_entry.side_effect = ValueError('Faltan ingredientes_seleccionados')
        r = client.post('/api/v1/planes-comida/plan-1/entradas', json={
            'fecha': '2024-01-01',
            'tipo_comida': 'almuerzo',
            'id_receta': 'rec-1',
        })
        assert r.status_code == 422

    def test_get_meal_list_returns_200(self, client, mock_mp):
        mock_mp.get_meal_plan.return_value = PLAN
        mock_mp.get_meal_list.return_value = []
        r = client.get('/api/v1/planes-comida/plan-1/lista-comidas')
        assert r.status_code == 200

    def test_get_meal_list_plan_not_found_returns_404(self, client, mock_mp):
        mock_mp.get_meal_plan.return_value = None
        r = client.get('/api/v1/planes-comida/nonexistent/lista-comidas')
        assert r.status_code == 404

    def test_get_grocery_list_returns_200(self, client, mock_mp):
        mock_mp.get_meal_plan.return_value = PLAN
        mock_mp.get_grocery_list.return_value = {'requeridos': [], 'opcionales': []}
        r = client.get('/api/v1/planes-comida/plan-1/lista-compras')
        assert r.status_code == 200
        assert 'requeridos' in r.json()

    def test_get_grocery_list_plan_not_found_returns_404(self, client, mock_mp):
        mock_mp.get_meal_plan.return_value = None
        r = client.get('/api/v1/planes-comida/nonexistent/lista-compras')
        assert r.status_code == 404
