from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Materia(Base):
    __tablename__ = "materias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))

    # cascade: al borrar una materia se borran sus notas (si no, quedarían huérfanas
    # o la base rechazaría el borrado por la clave foránea).
    notas: Mapped[list["Nota"]] = relationship(
        back_populates="materia", cascade="all, delete-orphan"
    )


class Nota(Base):
    __tablename__ = "notas"

    id: Mapped[int] = mapped_column(primary_key=True)
    materia_id: Mapped[int] = mapped_column(ForeignKey("materias.id"))
    valor: Mapped[float] = mapped_column(Float)

    materia: Mapped["Materia"] = relationship(back_populates="notas")
