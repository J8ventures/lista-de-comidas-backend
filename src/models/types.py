from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

NutritionalGroup = Literal['PROTEINS', 'CARBOHYDRATES', 'VEGETABLES', 'FRUITS', 'DAIRY', 'FATS', 'LEGUMES', 'GRAINS', 'OTHER']
IngredientRole = Literal['required', 'replaceable', 'optional']
MealType = Literal['breakfast', 'lunch', 'dinner', 'snack']
PlanType = Literal['weekly', 'biweekly']


# Pydantic models for API request/response validation
class AlternativeModel(BaseModel):
    ingredient_id: str
    quantity: float
    unit: str


class RecipeIngredientModel(BaseModel):
    ingredient_id: str
    role: IngredientRole
    quantity: float
    unit: str
    alternatives: list[AlternativeModel] = Field(default_factory=list)


class IngredientCreate(BaseModel):
    name: str
    nutritional_group: NutritionalGroup
    unit: str


class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    nutritional_group: Optional[NutritionalGroup] = None
    unit: Optional[str] = None


class RecipeCreate(BaseModel):
    name: str
    description: str = ""
    servings: int = 1
    prep_time: int = 0  # minutes
    cook_time: int = 0  # minutes
    ingredients: list[RecipeIngredientModel] = Field(default_factory=list)


class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    servings: Optional[int] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    ingredients: Optional[list[RecipeIngredientModel]] = None


class MealPlanEntryCreate(BaseModel):
    date: str  # ISO format YYYY-MM-DD
    meal_type: MealType
    recipe_id: str
    selected_ingredients: dict[str, str] = Field(default_factory=dict)  # replaceable_ingredient_id -> chosen_ingredient_id


class MealPlanCreate(BaseModel):
    name: str
    type: PlanType
    start_date: str  # ISO format YYYY-MM-DD
    end_date: str  # ISO format YYYY-MM-DD
    entries: list[MealPlanEntryCreate] = Field(default_factory=list)


class MealPlanUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[PlanType] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
