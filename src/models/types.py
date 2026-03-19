from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

GrupoNutricional = Literal['PROTEINAS', 'CARBOHIDRATOS', 'VERDURAS', 'FRUTAS', 'LACTEOS', 'GRASAS', 'LEGUMBRES', 'CEREALES', 'OTRO']
RolIngrediente = Literal['requerido', 'reemplazable', 'opcional']
TipoComida = Literal['desayuno', 'almuerzo', 'cena', 'merienda']
TipoPlan = Literal['semanal', 'quincenal']


# Modelos Pydantic para validación de request/response
class AlternativaModelo(BaseModel):
    id_ingrediente: str
    cantidad: float
    unidad: str


class IngredienteRecetaModelo(BaseModel):
    id_ingrediente: str
    rol: RolIngrediente
    cantidad: float
    unidad: str
    alternativas: list[AlternativaModelo] = Field(default_factory=list)


class IngredienteCrear(BaseModel):
    nombre: str
    grupo_nutricional: GrupoNutricional
    unidad: str


class IngredienteActualizar(BaseModel):
    nombre: Optional[str] = None
    grupo_nutricional: Optional[GrupoNutricional] = None
    unidad: Optional[str] = None


class RecetaCrear(BaseModel):
    nombre: str
    descripcion: str = ""
    porciones: int = 1
    tiempo_preparacion: int = 0  # minutos
    tiempo_coccion: int = 0  # minutos
    ingredientes: list[IngredienteRecetaModelo] = Field(default_factory=list)


class RecetaActualizar(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    porciones: Optional[int] = None
    tiempo_preparacion: Optional[int] = None
    tiempo_coccion: Optional[int] = None
    ingredientes: Optional[list[IngredienteRecetaModelo]] = None


class EntradaPlanCrear(BaseModel):
    fecha: str  # formato ISO YYYY-MM-DD
    tipo_comida: TipoComida
    id_receta: str
    ingredientes_seleccionados: dict[str, str] = Field(default_factory=dict)  # id_ingrediente_reemplazable -> id_ingrediente_elegido


class PlanComidaCrear(BaseModel):
    nombre: str
    tipo: TipoPlan
    fecha_inicio: str  # formato ISO YYYY-MM-DD
    fecha_fin: str  # formato ISO YYYY-MM-DD
    entradas: list[EntradaPlanCrear] = Field(default_factory=list)


class PlanComidaActualizar(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[TipoPlan] = None
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
