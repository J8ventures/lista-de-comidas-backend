"""Unit tests for all repository classes — DynamoDB calls are mocked via self._table."""

from unittest.mock import MagicMock, patch

from repositories.ingredients_repository import IngredientsRepository
from repositories.meal_plans_repository import MealPlansRepository
from repositories.recipes_repository import RecipesRepository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_repo(cls):
    """Instantiate a repository with a mocked DynamoDB table."""
    repo = cls.__new__(cls)
    repo._table = MagicMock()
    return repo


# ---------------------------------------------------------------------------
# IngredientsRepository
# ---------------------------------------------------------------------------


class TestIngredientsRepository:
    def setup_method(self):
        self.repo = make_repo(IngredientsRepository)
        self.table = self.repo._table

    def test_list_all_no_filter(self):
        self.table.query.return_value = {"Items": [{"id": "1"}]}
        result = self.repo.list_all()
        assert result == [{"id": "1"}]
        self.table.query.assert_called_once()
        call_kwargs = self.table.query.call_args.kwargs
        assert call_kwargs["IndexName"] == "GSI1"

    def test_list_all_with_group_filter(self):
        self.table.query.return_value = {"Items": [{"id": "1"}]}
        result = self.repo.list_all(grupo_nutricional="PROTEINAS")
        assert len(result) == 1
        call_kwargs = self.table.query.call_args.kwargs
        assert call_kwargs["IndexName"] == "GSI2"

    def test_list_all_empty_response(self):
        self.table.query.return_value = {}
        assert self.repo.list_all() == []

    def test_get_by_id_found(self):
        item = {"id": "ing-1", "nombre": "Pollo"}
        self.table.get_item.return_value = {"Item": item}
        assert self.repo.get_by_id("ing-1") == item

    def test_get_by_id_not_found(self):
        self.table.get_item.return_value = {}
        assert self.repo.get_by_id("nope") is None

    def test_create(self):
        self.table.put_item.return_value = {}
        data = {"nombre": "Arroz", "grupo_nutricional": "CARBOHIDRATOS", "unidad": "g"}
        result = self.repo.create(data)
        assert result["nombre"] == "Arroz"
        assert result["PK"].startswith("INGREDIENTE#")
        assert result["SK"] == "METADATA"
        self.table.put_item.assert_called_once()

    def test_update_not_found(self):
        self.table.get_item.return_value = {}
        assert self.repo.update("nope", {"nombre": "X"}) is None

    def test_update_nombre(self):
        existing = {"id": "ing-1", "nombre": "Pollo"}
        self.table.get_item.return_value = {"Item": existing}
        updated = {**existing, "nombre": "Pechuga"}
        self.table.update_item.return_value = {"Attributes": updated}
        result = self.repo.update("ing-1", {"nombre": "Pechuga"})
        assert result["nombre"] == "Pechuga"

    def test_update_grupo_nutricional(self):
        existing = {"id": "ing-1", "nombre": "Pollo", "grupo_nutricional": "PROTEINAS"}
        self.table.get_item.return_value = {"Item": existing}
        updated = {**existing, "grupo_nutricional": "OTROS"}
        self.table.update_item.return_value = {"Attributes": updated}
        result = self.repo.update("ing-1", {"grupo_nutricional": "OTROS"})
        assert result["grupo_nutricional"] == "OTROS"

    def test_update_unidad(self):
        existing = {"id": "ing-1", "nombre": "Pollo", "unidad": "g"}
        self.table.get_item.return_value = {"Item": existing}
        updated = {**existing, "unidad": "kg"}
        self.table.update_item.return_value = {"Attributes": updated}
        result = self.repo.update("ing-1", {"unidad": "kg"})
        assert result["unidad"] == "kg"

    def test_delete_found(self):
        self.table.get_item.return_value = {"Item": {"id": "ing-1"}}
        assert self.repo.delete("ing-1") is True
        self.table.delete_item.assert_called_once()

    def test_delete_not_found(self):
        self.table.get_item.return_value = {}
        assert self.repo.delete("nope") is False

    def test_get_batch_empty(self):
        assert self.repo.get_batch([]) == []

    def test_get_batch_single_chunk(self):
        item = {"id": "ing-1", "PK": "INGREDIENTE#ing-1", "SK": "METADATA"}
        self.table.meta.client.batch_get_item.return_value = {
            "Responses": {self.table.name: [item]}
        }
        result = self.repo.get_batch(["ing-1"])
        assert result == [item]

    def test_get_batch_multiple_chunks(self):
        """Verify batching splits keys into chunks of 100."""
        ids = [f"id-{i}" for i in range(150)]
        self.table.meta.client.batch_get_item.return_value = {
            "Responses": {self.table.name: []}
        }
        self.repo.get_batch(ids)
        assert self.table.meta.client.batch_get_item.call_count == 2


# ---------------------------------------------------------------------------
# RecipesRepository
# ---------------------------------------------------------------------------


class TestRecipesRepository:
    def setup_method(self):
        self.repo = make_repo(RecipesRepository)
        self.table = self.repo._table

    def test_list_all(self):
        self.table.query.return_value = {"Items": [{"id": "r1"}]}
        result = self.repo.list_all()
        assert result == [{"id": "r1"}]
        assert self.table.query.call_args.kwargs["IndexName"] == "GSI1"

    def test_list_all_empty(self):
        self.table.query.return_value = {}
        assert self.repo.list_all() == []

    def test_get_by_id_found(self):
        item = {"id": "r1", "nombre": "Pollo al horno"}
        self.table.get_item.return_value = {"Item": item}
        assert self.repo.get_by_id("r1") == item

    def test_get_by_id_not_found(self):
        self.table.get_item.return_value = {}
        assert self.repo.get_by_id("nope") is None

    def test_get_ingredients(self):
        items = [{"PK": "RECETA#r1", "SK": "INGREDIENTE#i1"}]
        self.table.query.return_value = {"Items": items}
        result = self.repo.get_ingredients("r1")
        assert result == items

    def test_get_ingredients_empty(self):
        self.table.query.return_value = {}
        assert self.repo.get_ingredients("r1") == []

    def test_get_recipes_by_ingredient(self):
        items = [{"GSI3PK": "INGREDIENTE#i1", "GSI3SK": "RECETA#r1"}]
        self.table.query.return_value = {"Items": items}
        result = self.repo.get_recipes_by_ingredient("i1")
        assert result == items
        assert self.table.query.call_args.kwargs["IndexName"] == "GSI3"

    def test_create(self):
        self.table.put_item.return_value = {}
        data = {"nombre": "Ensalada", "descripcion": "Fresca", "porciones": 2}
        result = self.repo.create(data)
        assert result["nombre"] == "Ensalada"
        assert result["PK"].startswith("RECETA#")

    def test_create_defaults(self):
        self.table.put_item.return_value = {}
        result = self.repo.create({"nombre": "Simple"})
        assert result["porciones"] == 1
        assert result["tiempo_preparacion"] == 0
        assert result["tiempo_coccion"] == 0

    def test_update_not_found(self):
        self.table.get_item.return_value = {}
        assert self.repo.update("nope", {"nombre": "X"}) is None

    def test_update_fields(self):
        existing = {"id": "r1", "nombre": "Viejo"}
        self.table.get_item.return_value = {"Item": existing}
        updated = {**existing, "nombre": "Nuevo", "porciones": 4}
        self.table.update_item.return_value = {"Attributes": updated}
        result = self.repo.update(
            "r1",
            {
                "nombre": "Nuevo",
                "descripcion": "desc",
                "porciones": 4,
                "tiempo_preparacion": 10,
                "tiempo_coccion": 20,
            },
        )
        assert result["nombre"] == "Nuevo"

    def test_delete_found_no_ingredients(self):
        self.table.get_item.return_value = {"Item": {"id": "r1"}}
        # get_ingredients returns empty
        self.table.query.return_value = {"Items": []}
        batch_writer = MagicMock()
        self.table.batch_writer.return_value.__enter__ = MagicMock(
            return_value=batch_writer
        )
        self.table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)
        assert self.repo.delete("r1") is True

    def test_delete_found_with_ingredients(self):
        self.table.get_item.return_value = {"Item": {"id": "r1"}}
        self.table.query.return_value = {
            "Items": [{"PK": "RECETA#r1", "SK": "INGREDIENTE#i1"}]
        }
        batch_writer = MagicMock()
        self.table.batch_writer.return_value.__enter__ = MagicMock(
            return_value=batch_writer
        )
        self.table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)
        assert self.repo.delete("r1") is True
        assert batch_writer.delete_item.call_count == 2

    def test_delete_not_found(self):
        self.table.get_item.return_value = {}
        assert self.repo.delete("nope") is False

    def test_set_ingredients(self):
        existing = [{"PK": "RECETA#r1", "SK": "INGREDIENTE#old"}]
        self.table.query.return_value = {"Items": existing}
        batch_writer = MagicMock()
        self.table.batch_writer.return_value.__enter__ = MagicMock(
            return_value=batch_writer
        )
        self.table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)
        new_ings = [
            {
                "id_ingrediente": "i2",
                "rol": "required",
                "cantidad": 100,
                "unidad": "g",
                "alternativas": [],
            }
        ]
        self.repo.set_ingredients("r1", new_ings)
        # deleted old + put new
        assert batch_writer.delete_item.call_count == 1
        assert batch_writer.put_item.call_count == 1

    def test_set_ingredients_no_alternativas(self):
        self.table.query.return_value = {"Items": []}
        batch_writer = MagicMock()
        self.table.batch_writer.return_value.__enter__ = MagicMock(
            return_value=batch_writer
        )
        self.table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)
        new_ings = [
            {"id_ingrediente": "i3", "rol": "optional", "cantidad": 50, "unidad": "ml"}
        ]
        self.repo.set_ingredients("r1", new_ings)
        put_call = batch_writer.put_item.call_args.kwargs["Item"]
        assert put_call["alternativas"] == []


# ---------------------------------------------------------------------------
# MealPlansRepository
# ---------------------------------------------------------------------------


class TestMealPlansRepository:
    def setup_method(self):
        self.repo = make_repo(MealPlansRepository)
        self.table = self.repo._table

    def test_list_all(self):
        self.table.query.return_value = {"Items": [{"id": "p1"}]}
        result = self.repo.list_all()
        assert result == [{"id": "p1"}]
        assert self.table.query.call_args.kwargs["IndexName"] == "GSI1"

    def test_list_all_empty(self):
        self.table.query.return_value = {}
        assert self.repo.list_all() == []

    def test_get_by_id_found(self):
        item = {"id": "p1", "nombre": "Semana 1"}
        self.table.get_item.return_value = {"Item": item}
        assert self.repo.get_by_id("p1") == item

    def test_get_by_id_not_found(self):
        self.table.get_item.return_value = {}
        assert self.repo.get_by_id("nope") is None

    def test_get_entries(self):
        entries = [{"PK": "PLANCOMIDA#p1", "SK": "ENTRADA#2024-01-01#desayuno#e1"}]
        self.table.query.return_value = {"Items": entries}
        result = self.repo.get_entries("p1")
        assert result == entries

    def test_get_entries_empty(self):
        self.table.query.return_value = {}
        assert self.repo.get_entries("p1") == []

    def test_create(self):
        self.table.put_item.return_value = {}
        data = {
            "nombre": "Plan semanal",
            "tipo": "semanal",
            "fecha_inicio": "2024-01-01",
            "fecha_fin": "2024-01-07",
        }
        result = self.repo.create(data)
        assert result["nombre"] == "Plan semanal"
        assert result["PK"].startswith("PLANCOMIDA#")
        assert result["SK"] == "METADATA"

    def test_update_not_found(self):
        self.table.get_item.return_value = {}
        assert self.repo.update("nope", {"nombre": "X"}) is None

    def test_update_fields(self):
        existing = {"id": "p1", "nombre": "Viejo"}
        self.table.get_item.return_value = {"Item": existing}
        updated = {**existing, "nombre": "Nuevo", "tipo": "quincenal"}
        self.table.update_item.return_value = {"Attributes": updated}
        result = self.repo.update(
            "p1",
            {
                "nombre": "Nuevo",
                "tipo": "quincenal",
                "fecha_inicio": "2024-02-01",
                "fecha_fin": "2024-02-15",
            },
        )
        assert result["nombre"] == "Nuevo"

    def test_delete_found_no_entries(self):
        self.table.get_item.return_value = {"Item": {"id": "p1"}}
        self.table.query.return_value = {"Items": []}
        batch_writer = MagicMock()
        self.table.batch_writer.return_value.__enter__ = MagicMock(
            return_value=batch_writer
        )
        self.table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)
        assert self.repo.delete("p1") is True

    def test_delete_found_with_entries(self):
        self.table.get_item.return_value = {"Item": {"id": "p1"}}
        self.table.query.return_value = {
            "Items": [{"PK": "PLANCOMIDA#p1", "SK": "ENTRADA#2024-01-01#almuerzo#e1"}]
        }
        batch_writer = MagicMock()
        self.table.batch_writer.return_value.__enter__ = MagicMock(
            return_value=batch_writer
        )
        self.table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)
        assert self.repo.delete("p1") is True
        assert batch_writer.delete_item.call_count == 2

    def test_delete_not_found(self):
        self.table.get_item.return_value = {}
        assert self.repo.delete("nope") is False

    def test_add_entry(self):
        self.table.put_item.return_value = {}
        datos = {
            "fecha": "2024-01-01",
            "tipo_comida": "desayuno",
            "id_receta": "r1",
            "ingredientes_seleccionados": {"i1": "i2"},
        }
        result = self.repo.add_entry("p1", datos)
        assert result["id_receta"] == "r1"
        assert result["fecha"] == "2024-01-01"
        assert result["SK"].startswith("ENTRADA#2024-01-01#desayuno#")
        self.table.put_item.assert_called_once()

    def test_add_entry_no_selected_ingredients(self):
        self.table.put_item.return_value = {}
        datos = {"fecha": "2024-01-02", "tipo_comida": "cena", "id_receta": "r2"}
        result = self.repo.add_entry("p1", datos)
        assert result["ingredientes_seleccionados"] == {}


# ---------------------------------------------------------------------------
# BaseRepository / utils.dynamodb
# ---------------------------------------------------------------------------


class TestBaseRepositoryTableProperty:
    def test_table_lazy_loads_via_get_table(self):
        from repositories.ingredients_repository import IngredientsRepository

        mock_table = MagicMock()
        with patch("repositories.base_repository.get_table", return_value=mock_table):
            repo = IngredientsRepository()
            t = repo.table  # first access — triggers get_table
            assert t is mock_table
            t2 = repo.table  # second access — cached, get_table NOT called again
            assert t2 is mock_table


class TestDynamoDBUtils:
    def setup_method(self):
        import utils.dynamodb as db_mod

        db_mod.reset_clients()

    def teardown_method(self):
        import utils.dynamodb as db_mod

        db_mod.reset_clients()

    def test_get_table_returns_table(self):
        from utils.dynamodb import get_table

        mock_resource = MagicMock()
        mock_table = MagicMock()
        mock_resource.Table.return_value = mock_table
        with patch("utils.dynamodb.get_dynamodb_resource", return_value=mock_resource):
            result = get_table()
        assert result is mock_table

    def test_get_table_caches(self):
        from utils.dynamodb import get_table

        mock_resource = MagicMock()
        mock_table = MagicMock()
        mock_resource.Table.return_value = mock_table
        with patch("utils.dynamodb.get_dynamodb_resource", return_value=mock_resource):
            t1 = get_table()
            t2 = get_table()
        assert t1 is t2
        assert mock_resource.Table.call_count == 1

    def test_get_dynamodb_resource_with_endpoint_url(self):
        import os

        from utils.dynamodb import get_dynamodb_resource

        with patch.dict(os.environ, {"DYNAMODB_ENDPOINT_URL": "http://localhost:8000"}):
            with patch("utils.dynamodb.boto3.resource") as mock_boto:
                mock_boto.return_value = MagicMock()
                get_dynamodb_resource()
                mock_boto.assert_called_once()
                call_kwargs = mock_boto.call_args.kwargs
                assert call_kwargs["endpoint_url"] == "http://localhost:8000"

    def test_get_dynamodb_resource_without_endpoint_url(self):
        import os

        from utils.dynamodb import get_dynamodb_resource

        env = {k: v for k, v in os.environ.items() if k != "DYNAMODB_ENDPOINT_URL"}
        with patch.dict(os.environ, env, clear=True):
            with patch("utils.dynamodb.boto3.resource") as mock_boto:
                mock_boto.return_value = MagicMock()
                get_dynamodb_resource()
                mock_boto.assert_called_once()
                call_kwargs = mock_boto.call_args
                assert "endpoint_url" not in (call_kwargs.kwargs or {})

    def test_reset_clients(self):
        import utils.dynamodb as db_mod

        db_mod._dynamodb_resource = MagicMock()
        db_mod._table = MagicMock()
        db_mod.reset_clients()
        assert db_mod._dynamodb_resource is None
        assert db_mod._table is None


class TestResponseUtils:
    def test_success_default_status(self):
        import json

        from utils.response import success

        r = success({"key": "value"})
        assert r["statusCode"] == 200
        assert json.loads(r["body"]) == {"key": "value"}
        assert "Access-Control-Allow-Origin" in r["headers"]

    def test_success_custom_status(self):
        from utils.response import success

        r = success({}, status_code=201)
        assert r["statusCode"] == 201

    def test_error_default_status(self):
        import json

        from utils.response import error

        r = error("bad request")
        assert r["statusCode"] == 400
        assert json.loads(r["body"]) == {"error": "bad request"}

    def test_error_custom_status(self):
        from utils.response import error

        r = error("forbidden", status_code=403)
        assert r["statusCode"] == 403

    def test_not_found(self):
        import json

        from utils.response import not_found

        r = not_found("Ingredient")
        assert r["statusCode"] == 404
        assert "Ingredient not found" in json.loads(r["body"])["error"]

    def test_not_found_default_resource(self):
        import json

        from utils.response import not_found

        r = not_found()
        assert "Resource not found" in json.loads(r["body"])["error"]

    def test_internal_error(self):
        import json

        from utils.response import internal_error

        r = internal_error()
        assert r["statusCode"] == 500
        assert "Internal server error" in json.loads(r["body"])["error"]

    def test_internal_error_custom_message(self):
        from utils.response import internal_error

        r = internal_error("DB timeout")
        assert r["statusCode"] == 500
