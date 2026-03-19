import uuid
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from repositories.base_repository import BaseRepository


class RecipesRepository(BaseRepository):
    def list_all(self) -> list[dict]:
        response = self.table.query(
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq('RECETA'),
        )
        return response.get('Items', [])

    def get_by_id(self, id_receta: str) -> dict | None:
        response = self.table.get_item(
            Key={'PK': f'RECETA#{id_receta}', 'SK': 'METADATA'}
        )
        return response.get('Item')

    def get_ingredients(self, id_receta: str) -> list[dict]:
        response = self.table.query(
            KeyConditionExpression=Key('PK').eq(f'RECETA#{id_receta}') & Key('SK').begins_with('INGREDIENTE#')
        )
        return response.get('Items', [])

    def get_recipes_by_ingredient(self, id_ingrediente: str) -> list[dict]:
        response = self.table.query(
            IndexName='GSI3',
            KeyConditionExpression=Key('GSI3PK').eq(f'INGREDIENTE#{id_ingrediente}'),
        )
        return response.get('Items', [])

    def create(self, data: dict) -> dict:
        id_receta = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            'PK': f'RECETA#{id_receta}',
            'SK': 'METADATA',
            'GSI1PK': 'RECETA',
            'GSI1SK': now,
            'id': id_receta,
            'nombre': data['nombre'],
            'descripcion': data.get('descripcion', ''),
            'porciones': data.get('porciones', 1),
            'tiempo_preparacion': data.get('tiempo_preparacion', 0),
            'tiempo_coccion': data.get('tiempo_coccion', 0),
            'creado_en': now,
            'actualizado_en': now,
        }
        self.table.put_item(Item=item)
        return item

    def update(self, id_receta: str, data: dict) -> dict | None:
        existing = self.get_by_id(id_receta)
        if not existing:
            return None
        now = datetime.now(timezone.utc).isoformat()
        update_expressions = ['#actualizado_en = :actualizado_en']
        expression_values = {':actualizado_en': now}
        expression_names = {'#actualizado_en': 'actualizado_en'}

        fields = ['nombre', 'descripcion', 'porciones', 'tiempo_preparacion', 'tiempo_coccion']
        for f in fields:
            if f in data:
                update_expressions.append(f'#{f} = :{f}')
                expression_values[f':{f}'] = data[f]
                expression_names[f'#{f}'] = f

        response = self.table.update_item(
            Key={'PK': f'RECETA#{id_receta}', 'SK': 'METADATA'},
            UpdateExpression='SET ' + ', '.join(update_expressions),
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names,
            ReturnValues='ALL_NEW',
        )
        return response['Attributes']

    def delete(self, id_receta: str) -> bool:
        existing = self.get_by_id(id_receta)
        if not existing:
            return False
        ingredientes = self.get_ingredients(id_receta)
        with self.table.batch_writer() as batch:
            batch.delete_item(Key={'PK': f'RECETA#{id_receta}', 'SK': 'METADATA'})
            for ing in ingredientes:
                batch.delete_item(Key={'PK': ing['PK'], 'SK': ing['SK']})
        return True

    def set_ingredients(self, id_receta: str, ingredientes: list[dict]):
        """Reemplaza todos los ingredientes de una receta."""
        existing = self.get_ingredients(id_receta)
        now = datetime.now(timezone.utc).isoformat()
        with self.table.batch_writer() as batch:
            for ing in existing:
                batch.delete_item(Key={'PK': ing['PK'], 'SK': ing['SK']})
            for ing in ingredientes:
                item = {
                    'PK': f'RECETA#{id_receta}',
                    'SK': f'INGREDIENTE#{ing["id_ingrediente"]}',
                    'GSI3PK': f'INGREDIENTE#{ing["id_ingrediente"]}',
                    'GSI3SK': f'RECETA#{id_receta}',
                    'id_ingrediente': ing['id_ingrediente'],
                    'rol': ing['rol'],
                    'cantidad': str(ing['cantidad']),
                    'unidad': ing['unidad'],
                    'alternativas': ing.get('alternativas', []),
                    'creado_en': now,
                }
                batch.put_item(Item=item)
