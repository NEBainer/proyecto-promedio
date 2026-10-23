import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# En producción (Render) viene de la variable de entorno DATABASE_URL.
# En local, si no existe, usamos un SQLite para poder desarrollar sin Postgres.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")

# Supabase/Render pueden entregar "postgres://" o "postgresql://". Desde SQLAlchemy 2.1
# el driver por defecto de "postgresql://" es psycopg (v3), pero acá instalamos
# psycopg2, así que lo indicamos explícitamente.
for prefijo in ("postgres://", "postgresql://"):
    if DATABASE_URL.startswith(prefijo):
        DATABASE_URL = "postgresql+psycopg2://" + DATABASE_URL[len(prefijo):]
        break

# check_same_thread solo aplica a SQLite.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# pool_pre_ping verifica que la conexión siga viva antes de usarla.
# Importa con el free tier: las conexiones inactivas se cortan.
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: una sesión por request, siempre se cierra."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
