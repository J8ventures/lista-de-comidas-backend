import uuid
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from repositories.base_repository import BaseRepository


class MealPlansRepository(BaseRepository):
    def list_all(self) -> list[dict]:
        response = self.table.query(
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq('MEALPLAN'),
        )
        return response.get('Items', [])

    def get_by_id(self, plan_id: str) -> dict | None:
        response = self.table.get_item(
            Key={'PK': f'MEALPLAN#{plan_id}', 'SK': 'METADATA'}
        )
        return response.get('Item')

    def get_entries(self, plan_id: str) -> list[dict]:
        response = self.table.query(
            KeyConditionExpression=Key('PK').eq(f'MEALPLAN#{plan_id}') & Key('SK').begins_with('ENTRY#')
        )
        return response.get('Items', [])

    def create(self, data: dict) -> dict:
        plan_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            'PK': f'MEALPLAN#{plan_id}',
            'SK': 'METADATA',
            'GSI1PK': 'MEALPLAN',
            'GSI1SK': now,
            'id': plan_id,
            'name': data['name'],
            'type': data['type'],
            'start_date': data['start_date'],
            'end_date': data['end_date'],
            'created_at': now,
            'updated_at': now,
        }
        self.table.put_item(Item=item)
        return item

    def update(self, plan_id: str, data: dict) -> dict | None:
        existing = self.get_by_id(plan_id)
        if not existing:
            return None
        now = datetime.now(timezone.utc).isoformat()
        update_expressions = ['#updated_at = :updated_at']
        expression_values = {':updated_at': now}
        expression_names = {'#updated_at': 'updated_at'}

        for f in ['name', 'type', 'start_date', 'end_date']:
            if f in data:
                update_expressions.append(f'#{f} = :{f}')
                expression_values[f':{f}'] = data[f]
                expression_names[f'#{f}'] = f

        response = self.table.update_item(
            Key={'PK': f'MEALPLAN#{plan_id}', 'SK': 'METADATA'},
            UpdateExpression='SET ' + ', '.join(update_expressions),
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names,
            ReturnValues='ALL_NEW',
        )
        return response['Attributes']

    def delete(self, plan_id: str) -> bool:
        existing = self.get_by_id(plan_id)
        if not existing:
            return False
        entries = self.get_entries(plan_id)
        with self.table.batch_writer() as batch:
            batch.delete_item(Key={'PK': f'MEALPLAN#{plan_id}', 'SK': 'METADATA'})
            for entry in entries:
                batch.delete_item(Key={'PK': entry['PK'], 'SK': entry['SK']})
        return True

    def add_entry(self, plan_id: str, entry_data: dict) -> dict:
        entry_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        sk = f'ENTRY#{entry_data["date"]}#{entry_data["meal_type"]}#{entry_id}'
        item = {
            'PK': f'MEALPLAN#{plan_id}',
            'SK': sk,
            'id': entry_id,
            'date': entry_data['date'],
            'meal_type': entry_data['meal_type'],
            'recipe_id': entry_data['recipe_id'],
            'selected_ingredients': entry_data.get('selected_ingredients', {}),
            'created_at': now,
        }
        self.table.put_item(Item=item)
        return item
