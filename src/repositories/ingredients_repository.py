import uuid
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from repositories.base_repository import BaseRepository


class IngredientsRepository(BaseRepository):
    def list_all(self, nutritional_group: str = None) -> list[dict]:
        if nutritional_group:
            response = self.table.query(
                IndexName='GSI2',
                KeyConditionExpression=Key('GSI2PK').eq(nutritional_group),
            )
        else:
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('GSI1PK').eq('INGREDIENT'),
            )
        return response.get('Items', [])

    def get_by_id(self, ingredient_id: str) -> dict | None:
        response = self.table.get_item(
            Key={'PK': f'INGREDIENT#{ingredient_id}', 'SK': 'METADATA'}
        )
        return response.get('Item')

    def create(self, data: dict) -> dict:
        ingredient_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            'PK': f'INGREDIENT#{ingredient_id}',
            'SK': 'METADATA',
            'GSI1PK': 'INGREDIENT',
            'GSI1SK': now,
            'GSI2PK': data['nutritional_group'],
            'GSI2SK': data['name'],
            'id': ingredient_id,
            'name': data['name'],
            'nutritional_group': data['nutritional_group'],
            'unit': data['unit'],
            'created_at': now,
            'updated_at': now,
        }
        self.table.put_item(Item=item)
        return item

    def update(self, ingredient_id: str, data: dict) -> dict | None:
        existing = self.get_by_id(ingredient_id)
        if not existing:
            return None
        now = datetime.now(timezone.utc).isoformat()
        update_expressions = ['#updated_at = :updated_at']
        expression_values = {':updated_at': now}
        expression_names = {'#updated_at': 'updated_at'}

        if 'name' in data:
            update_expressions.append('#name = :name')
            expression_values[':name'] = data['name']
            expression_names['#name'] = 'name'
            update_expressions.append('GSI2SK = :gsi2sk')
            expression_values[':gsi2sk'] = data['name']

        if 'nutritional_group' in data:
            update_expressions.append('nutritional_group = :nutritional_group')
            expression_values[':nutritional_group'] = data['nutritional_group']
            update_expressions.append('GSI2PK = :gsi2pk')
            expression_values[':gsi2pk'] = data['nutritional_group']

        if 'unit' in data:
            update_expressions.append('#unit = :unit')
            expression_values[':unit'] = data['unit']
            expression_names['#unit'] = 'unit'

        response = self.table.update_item(
            Key={'PK': f'INGREDIENT#{ingredient_id}', 'SK': 'METADATA'},
            UpdateExpression='SET ' + ', '.join(update_expressions),
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names if expression_names else None,
            ReturnValues='ALL_NEW',
        )
        return response['Attributes']

    def delete(self, ingredient_id: str) -> bool:
        existing = self.get_by_id(ingredient_id)
        if not existing:
            return False
        self.table.delete_item(
            Key={'PK': f'INGREDIENT#{ingredient_id}', 'SK': 'METADATA'}
        )
        return True

    def get_batch(self, ingredient_ids: list[str]) -> list[dict]:
        if not ingredient_ids:
            return []
        # DynamoDB batch_get_item supports up to 100 items
        keys = [{'PK': f'INGREDIENT#{iid}', 'SK': 'METADATA'} for iid in ingredient_ids]
        results = []
        for i in range(0, len(keys), 100):
            chunk = keys[i:i+100]
            table_name = self.table.name
            response = self.table.meta.client.batch_get_item(
                RequestItems={table_name: {'Keys': chunk}}
            )
            results.extend(response['Responses'].get(table_name, []))
        return results
