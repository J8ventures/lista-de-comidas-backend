from unittest.mock import patch

import pytest

from services.ingredients_service import IngredientsService

RAW_ITEM = {
    "id": "ing-1",
    "nombre": "Pollo",
    "grupo_nutricional": "PROTEINAS",
    "unidad": "g",
    "creado_en": "2024-01-01T00:00:00",
    "actualizado_en": "2024-01-01T00:00:00",
}

FORMATTED_ITEM = {
    "id": "ing-1",
    "nombre": "Pollo",
    "grupo_nutricional": "PROTEINAS",
    "unidad": "g",
    "creado_en": "2024-01-01T00:00:00",
    "actualizado_en": "2024-01-01T00:00:00",
}


@pytest.fixture
def service():
    with patch("services.ingredients_service.IngredientsRepository") as MockRepo:
        svc = IngredientsService()
        svc.repo = MockRepo()
        yield svc


def test_list_ingredients_all(service):
    service.repo.list_all.return_value = [RAW_ITEM]
    result = service.list_ingredients()
    service.repo.list_all.assert_called_once_with(None)
    assert result == [FORMATTED_ITEM]


def test_list_ingredients_filter_by_group(service):
    service.repo.list_all.return_value = [RAW_ITEM]
    result = service.list_ingredients(grupo_nutricional="PROTEINAS")
    service.repo.list_all.assert_called_once_with("PROTEINAS")
    assert len(result) == 1


def test_list_ingredients_empty(service):
    service.repo.list_all.return_value = []
    result = service.list_ingredients()
    assert result == []


def test_get_ingredient_found(service):
    service.repo.get_by_id.return_value = RAW_ITEM
    result = service.get_ingredient("ing-1")
    service.repo.get_by_id.assert_called_once_with("ing-1")
    assert result == FORMATTED_ITEM


def test_get_ingredient_not_found(service):
    service.repo.get_by_id.return_value = None
    result = service.get_ingredient("nonexistent")
    assert result is None


def test_create_ingredient(service):
    data = {"nombre": "Pollo", "grupo_nutricional": "PROTEINAS", "unidad": "g"}
    service.repo.create.return_value = RAW_ITEM
    result = service.create_ingredient(data)
    service.repo.create.assert_called_once_with(data)
    assert result == FORMATTED_ITEM


def test_update_ingredient_found(service):
    service.repo.update.return_value = {**RAW_ITEM, "nombre": "Pechuga"}
    result = service.update_ingredient("ing-1", {"nombre": "Pechuga"})
    assert result["nombre"] == "Pechuga"


def test_update_ingredient_not_found(service):
    service.repo.update.return_value = None
    result = service.update_ingredient("nonexistent", {"nombre": "X"})
    assert result is None


def test_delete_ingredient_found(service):
    service.repo.delete.return_value = True
    assert service.delete_ingredient("ing-1") is True


def test_delete_ingredient_not_found(service):
    service.repo.delete.return_value = False
    assert service.delete_ingredient("nonexistent") is False


def test_get_batch(service):
    service.repo.get_batch.return_value = [RAW_ITEM]
    result = service.get_batch(["ing-1"])
    service.repo.get_batch.assert_called_once_with(["ing-1"])
    assert "ing-1" in result
    assert result["ing-1"] == FORMATTED_ITEM


def test_format_strips_extra_fields(service):
    raw = {
        **RAW_ITEM,
        "PK": "INGREDIENT#ing-1",
        "SK": "METADATA",
        "GSI1PK": "INGREDIENT",
    }
    service.repo.get_by_id.return_value = raw
    result = service.get_ingredient("ing-1")
    assert "PK" not in result
    assert "SK" not in result
    assert "GSI1PK" not in result
