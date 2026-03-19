import uuid
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from repositories.base_repository import BaseRepository


class RecipesRepository(BaseRepository):
    def list_all(self) -> list[dict]:
        response = self.table.query(
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq('RECIPE'),
        )
        return response.get('Items', [])

    def get_by_id(self, recipe_id: str) -> dict | None:
        response = self.table.get_item(
            Key={'PK': f'RECIPE#{recipe_id}', 'SK': 'METADATA'}
        )
        return response.get('Item')

    def get_ingredients(self, recipe_id: str) -> list[dict]:
        response = self.table.query(
            KeyConditionExpression=Key('PK').eq(f'RECIPE#{recipe_id}') & Key('SK').begins_with('INGREDIENT#')
        )
        return response.get('Items', [])

    def get_recipes_by_ingredient(self, ingredient_id: str) -> list[dict]:
        response = self.table.query(
            IndexName='GSI3',
            KeyConditionExpression=Key('GSI3PK').eq(f'INGREDIENT#{ingredient_id}'),
        )
        return response.get('Items', [])

    def create(self, data: dict) -> dict:
        recipe_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            'PK': f'RECIPE#{recipe_id}',
            'SK': 'METADATA',
            'GSI1PK': 'RECIPE',
            'GSI1SK': now,
            'id': recipe_id,
            'name': data['name'],
            'description': data.get('description', ''),
            'servings': data.get('servings', 1),
            'prep_time': data.get('prep_time', 0),
            'cook_time': data.get('cook_time', 0),
            'created_at': now,
            'updated_at': now,
        }
        self.table.put_item(Item=item)
        return item

    def update(self, recipe_id: str, data: dict) -> dict | None:
        existing = self.get_by_id(recipe_id)
        if not existing:
            return None
        now = datetime.now(timezone.utc).isoformat()
        update_expressions = ['#updated_at = :updated_at']
        expression_values = {':updated_at': now}
        expression_names = {'#updated_at': 'updated_at'}

        fields = ['name', 'description', 'servings', 'prep_time', 'cook_time']
        for f in fields:
            if f in data:
                update_expressions.append(f'#{f} = :{f}')
                expression_values[f':{f}'] = data[f]
                expression_names[f'#{f}'] = f

        response = self.table.update_item(
            Key={'PK': f'RECIPE#{recipe_id}', 'SK': 'METADATA'},
            UpdateExpression='SET ' + ', '.join(update_expressions),
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names,
            ReturnValues='ALL_NEW',
        )
        return response['Attributes']

    def delete(self, recipe_id: str) -> bool:
        existing = self.get_by_id(recipe_id)
        if not existing:
            return False
        # Delete metadata + all ingredient rows
        ingredients = self.get_ingredients(recipe_id)
        with self.table.batch_writer() as batch:
            batch.delete_item(Key={'PK': f'RECIPE#{recipe_id}', 'SK': 'METADATA'})
            for ing in ingredients:
                batch.delete_item(Key={'PK': ing['PK'], 'SK': ing['SK']})
        return True

    def set_ingredients(self, recipe_id: str, ingredients: list[dict]):
        """Replace all recipe ingredients."""
        existing = self.get_ingredients(recipe_id)
        now = datetime.now(timezone.utc).isoformat()
        with self.table.batch_writer() as batch:
            for ing in existing:
                batch.delete_item(Key={'PK': ing['PK'], 'SK': ing['SK']})
            for ing in ingredients:
                item = {
                    'PK': f'RECIPE#{recipe_id}',
                    'SK': f'INGREDIENT#{ing["ingredient_id"]}',
                    'GSI3PK': f'INGREDIENT#{ing["ingredient_id"]}',
                    'GSI3SK': f'RECIPE#{recipe_id}',
                    'ingredient_id': ing['ingredient_id'],
                    'role': ing['role'],
                    'quantity': str(ing['quantity']),
                    'unit': ing['unit'],
                    'alternatives': ing.get('alternatives', []),
                    'created_at': now,
                }
                batch.put_item(Item=item)
