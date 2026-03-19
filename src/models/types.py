from typing import Literal

from pydantic import BaseModel, Field

GrupoNutricional = Literal[
    "PROTEINAS",
    "CARBOHIDRATOS",
    "VERDURAS",
    "FRUTAS",
    "LACTEOS",
    "GRASAS",
    "LEGUMBRES",
    "CEREALES",
    "OTRO",
]
RolIngrediente = Literal["requerido", "reemplazable", "opcional"]
TipoComida = Literal["desayuno", "almuerzo", "cena", "merienda"]
TipoPlan = Literal["semanal", "quincenal"]


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
    nombre: str | None = None
    grupo_nutricional: GrupoNutricional | None = None
    unidad: str | None = None


class RecetaCrear(BaseModel):
    nombre: str
    descripcion: str = ""
    porciones: int = 1
    tiempo_preparacion: int = 0  # minutos
    tiempo_coccion: int = 0  # minutos
    ingredientes: list[IngredienteRecetaModelo] = Field(default_factory=list)


class RecetaActualizar(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    porciones: int | None = None
    tiempo_preparacion: int | None = None
    tiempo_coccion: int | None = None
    ingredientes: list[IngredienteRecetaModelo] | None = None


class EntradaPlanCrear(BaseModel):
    fecha: str  # formato ISO YYYY-MM-DD
    tipo_comida: TipoComida
    id_receta: str
    ingredientes_seleccionados: dict[str, str] = Field(
        default_factory=dict
    )  # id_ingrediente_reemplazable -> id_ingrediente_elegido


class PlanComidaCrear(BaseModel):
    nombre: str
    tipo: TipoPlan
    fecha_inicio: str  # formato ISO YYYY-MM-DD
    fecha_fin: str  # formato ISO YYYY-MM-DD
    entradas: list[EntradaPlanCrear] = Field(default_factory=list)


class PlanComidaActualizar(BaseModel):
    nombre: str | None = None
    tipo: TipoPlan | None = None
    fecha_inicio: str | None = None
    fecha_fin: str | None = None
