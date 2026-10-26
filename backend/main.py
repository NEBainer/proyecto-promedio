import os
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, engine, get_db

# Sentry se activa solo si existe la variable SENTRY_DSN (el DSN nunca va en el repo).
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea las tablas si no existen. Alcanza para este TP;
    # en un proyecto real usaríamos migraciones (Alembic).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Promedio de cursada", lifespan=lifespan)


# Los errores no controlados (500) se generan FUERA del CORSMiddleware, así que
# salían sin cabeceras CORS y el navegador solo veía "Failed to fetch".
# Este middleware queda por DENTRO de CORS: atrapa la excepción, la manda a
# Sentry y devuelve un 500 en JSON que el frontend sí puede leer.
@app.middleware("http")
async def errores_a_sentry(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        sentry_sdk.capture_exception(exc)
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error interno: {type(exc).__name__}"},
        )

# Orígenes permitidos, separados por coma. En Render se agrega el dominio de Netlify.
origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5500,http://127.0.0.1:5500",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/materias", response_model=list[schemas.MateriaOut])
def listar_materias(db: Session = Depends(get_db)):
    return db.scalars(select(models.Materia).order_by(models.Materia.id)).all()


@app.post("/materias", response_model=schemas.MateriaOut, status_code=201)
def crear_materia(datos: schemas.MateriaCreate, db: Session = Depends(get_db)):
    materia = models.Materia(nombre=datos.nombre)
    db.add(materia)
    db.commit()
    db.refresh(materia)
    return materia


@app.delete("/materias/{materia_id}", status_code=204)
def borrar_materia(materia_id: int, db: Session = Depends(get_db)):
    materia = db.get(models.Materia, materia_id)
    if materia is None:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    db.delete(materia)
    db.commit()
    return Response(status_code=204)


@app.post(
    "/materias/{materia_id}/notas", response_model=schemas.NotaOut, status_code=201
)
def agregar_nota(
    materia_id: int, datos: schemas.NotaCreate, db: Session = Depends(get_db)
):
    if db.get(models.Materia, materia_id) is None:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    nota = models.Nota(materia_id=materia_id, valor=datos.valor)
    db.add(nota)
    db.commit()
    db.refresh(nota)
    return nota


@app.get("/materias/{materia_id}/promedio")
def promedio_materia(materia_id: int, db: Session = Depends(get_db)):
    materia = db.get(models.Materia, materia_id)
    if materia is None:
        raise HTTPException(status_code=404, detail="Materia no encontrada")

    notas = [n.valor for n in materia.notas]
    # Sin notas no hay promedio: devolvemos null en vez de dividir por cero
    # (antes era el ZeroDivisionError a propósito que mostramos en Sentry).
    if not notas:
        return {"promedio": None}
    return {"promedio": sum(notas) / len(notas)}


@app.get("/promedio")
def promedio_general(db: Session = Depends(get_db)):
    notas = [n.valor for n in db.scalars(select(models.Nota)).all()]
    # Mismo caso: sin notas cargadas, null en vez de división por cero.
    if not notas:
        return {"promedio": None}
    return {"promedio": sum(notas) / len(notas)}


@app.get("/debug/boom")
def boom():
    # Respaldo para la demo: excepción forzada. Sacarlo (o protegerlo) después.
    raise RuntimeError("Error forzado para probar Sentry")
