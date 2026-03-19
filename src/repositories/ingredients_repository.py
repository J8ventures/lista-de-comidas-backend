import uuid
from datetime import UTC, datetime

from boto3.dynamodb.conditions import Key

from repositories.base_repository import BaseRepository


class IngredientsRepository(BaseRepository):
    def list_all(self, grupo_nutricional: str = None) -> list[dict]:
        if grupo_nutricional:
            response = self.table.query(
                IndexName="GSI2",
                KeyConditionExpression=Key("GSI2PK").eq(grupo_nutricional),
            )
        else:
            response = self.table.query(
                IndexName="GSI1",
                KeyConditionExpression=Key("GSI1PK").eq("INGREDIENTE"),
            )
        return response.get("Items", [])

    def get_by_id(self, id_ingrediente: str) -> dict | None:
        response = self.table.get_item(
            Key={"PK": f"INGREDIENTE#{id_ingrediente}", "SK": "METADATA"}
        )
        return response.get("Item")

    def create(self, data: dict) -> dict:
        id_ingrediente = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        item = {
            "PK": f"INGREDIENTE#{id_ingrediente}",
            "SK": "METADATA",
            "GSI1PK": "INGREDIENTE",
            "GSI1SK": now,
            "GSI2PK": data["grupo_nutricional"],
            "GSI2SK": data["nombre"],
            "id": id_ingrediente,
            "nombre": data["nombre"],
            "grupo_nutricional": data["grupo_nutricional"],
            "unidad": data["unidad"],
            "creado_en": now,
            "actualizado_en": now,
        }
        self.table.put_item(Item=item)
        return item

    def update(self, id_ingrediente: str, data: dict) -> dict | None:
        existing = self.get_by_id(id_ingrediente)
        if not existing:
            return None
        now = datetime.now(UTC).isoformat()
        update_expressions = ["#actualizado_en = :actualizado_en"]
        expression_values = {":actualizado_en": now}
        expression_names = {"#actualizado_en": "actualizado_en"}

        if "nombre" in data:
            update_expressions.append("#nombre = :nombre")
            expression_values[":nombre"] = data["nombre"]
            expression_names["#nombre"] = "nombre"
            update_expressions.append("GSI2SK = :gsi2sk")
            expression_values[":gsi2sk"] = data["nombre"]

        if "grupo_nutricional" in data:
            update_expressions.append("grupo_nutricional = :grupo_nutricional")
            expression_values[":grupo_nutricional"] = data["grupo_nutricional"]
            update_expressions.append("GSI2PK = :gsi2pk")
            expression_values[":gsi2pk"] = data["grupo_nutricional"]

        if "unidad" in data:
            update_expressions.append("#unidad = :unidad")
            expression_values[":unidad"] = data["unidad"]
            expression_names["#unidad"] = "unidad"

        response = self.table.update_item(
            Key={"PK": f"INGREDIENTE#{id_ingrediente}", "SK": "METADATA"},
            UpdateExpression="SET " + ", ".join(update_expressions),
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names if expression_names else None,
            ReturnValues="ALL_NEW",
        )
        return response["Attributes"]

    def delete(self, id_ingrediente: str) -> bool:
        existing = self.get_by_id(id_ingrediente)
        if not existing:
            return False
        self.table.delete_item(
            Key={"PK": f"INGREDIENTE#{id_ingrediente}", "SK": "METADATA"}
        )
        return True

    def get_batch(self, ids_ingrediente: list[str]) -> list[dict]:
        if not ids_ingrediente:
            return []
        keys = [
            {"PK": f"INGREDIENTE#{iid}", "SK": "METADATA"} for iid in ids_ingrediente
        ]
        results = []
        for i in range(0, len(keys), 100):
            chunk = keys[i : i + 100]
            table_name = self.table.name
            response = self.table.meta.client.batch_get_item(
                RequestItems={table_name: {"Keys": chunk}}
            )
            results.extend(response["Responses"].get(table_name, []))
        return results
