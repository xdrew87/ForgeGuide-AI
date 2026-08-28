from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import get_settings

_engine = None
_SessionLocal = None


def _get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def _get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())
    return _SessionLocal


# Compat alias
def SessionLocal():
    return _get_session_factory()()


class _SessionContext:
    """Context manager for session (used with `with SessionLocal() as sess`)."""
    def __enter__(self):
        self._sess = _get_session_factory()()
        return self._sess
    def __exit__(self, *args):
        self._sess.close()


# Monkey-patch SessionLocal to support `with SessionLocal() as s:`
import types

def _session_local_call():
    return _SessionContext()

SessionLocal = _session_local_call  # type: ignore


def get_db():
    db = _get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models.models import Base
    Base.metadata.create_all(bind=_get_engine())
