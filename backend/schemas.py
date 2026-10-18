from pydantic import BaseModel, ConfigDict, Field


class MateriaCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)


class MateriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class NotaCreate(BaseModel):
    # Validación de entrada: rechaza con 422 todo lo que no esté entre 0 y 10.
    valor: float = Field(ge=0, le=10)


class NotaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    materia_id: int
    valor: float
