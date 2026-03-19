import uuid
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from repositories.base_repository import BaseRepository


class MealPlansRepository(BaseRepository):
    def list_all(self) -> list[dict]:
        response = self.table.query(
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq('PLANCOMIDA'),
        )
        return response.get('Items', [])

    def get_by_id(self, id_plan: str) -> dict | None:
        response = self.table.get_item(
            Key={'PK': f'PLANCOMIDA#{id_plan}', 'SK': 'METADATA'}
        )
        return response.get('Item')

    def get_entries(self, id_plan: str) -> list[dict]:
        response = self.table.query(
            KeyConditionExpression=Key('PK').eq(f'PLANCOMIDA#{id_plan}') & Key('SK').begins_with('ENTRADA#')
        )
        return response.get('Items', [])

    def create(self, data: dict) -> dict:
        id_plan = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            'PK': f'PLANCOMIDA#{id_plan}',
            'SK': 'METADATA',
            'GSI1PK': 'PLANCOMIDA',
            'GSI1SK': now,
            'id': id_plan,
            'nombre': data['nombre'],
            'tipo': data['tipo'],
            'fecha_inicio': data['fecha_inicio'],
            'fecha_fin': data['fecha_fin'],
            'creado_en': now,
            'actualizado_en': now,
        }
        self.table.put_item(Item=item)
        return item

    def update(self, id_plan: str, data: dict) -> dict | None:
        existing = self.get_by_id(id_plan)
        if not existing:
            return None
        now = datetime.now(timezone.utc).isoformat()
        update_expressions = ['#actualizado_en = :actualizado_en']
        expression_values = {':actualizado_en': now}
        expression_names = {'#actualizado_en': 'actualizado_en'}

        for f in ['nombre', 'tipo', 'fecha_inicio', 'fecha_fin']:
            if f in data:
                update_expressions.append(f'#{f} = :{f}')
                expression_values[f':{f}'] = data[f]
                expression_names[f'#{f}'] = f

        response = self.table.update_item(
            Key={'PK': f'PLANCOMIDA#{id_plan}', 'SK': 'METADATA'},
            UpdateExpression='SET ' + ', '.join(update_expressions),
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names,
            ReturnValues='ALL_NEW',
        )
        return response['Attributes']

    def delete(self, id_plan: str) -> bool:
        existing = self.get_by_id(id_plan)
        if not existing:
            return False
        entradas = self.get_entries(id_plan)
        with self.table.batch_writer() as batch:
            batch.delete_item(Key={'PK': f'PLANCOMIDA#{id_plan}', 'SK': 'METADATA'})
            for entrada in entradas:
                batch.delete_item(Key={'PK': entrada['PK'], 'SK': entrada['SK']})
        return True

    def add_entry(self, id_plan: str, datos_entrada: dict) -> dict:
        id_entrada = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        sk = f'ENTRADA#{datos_entrada["fecha"]}#{datos_entrada["tipo_comida"]}#{id_entrada}'
        item = {
            'PK': f'PLANCOMIDA#{id_plan}',
            'SK': sk,
            'id': id_entrada,
            'fecha': datos_entrada['fecha'],
            'tipo_comida': datos_entrada['tipo_comida'],
            'id_receta': datos_entrada['id_receta'],
            'ingredientes_seleccionados': datos_entrada.get('ingredientes_seleccionados', {}),
            'creado_en': now,
        }
        self.table.put_item(Item=item)
        return item
