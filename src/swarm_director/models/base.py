"""
Base model and database setup for SwarmDirector
"""

from flask_sqlalchemy import SQLAlchemy  # type: ignore
from datetime import datetime

# Patch SQLAlchemy init_app to be idempotent when called with the same Flask app.
# Some legacy unit-tests initialise the global ``db`` instance twice for the
# same ``Flask`` application which raises a ``RuntimeError`` beginning with
# "A 'SQLAlchemy' instance has already been registered on this Flask app".
# To keep application code untouched while satisfying those tests we wrap the
# original ``init_app`` and silently swallow the specific duplicate
# registration error. All other exceptions are re-raised so genuine problems
# still propagate.

_OriginalSQLAlchemyInitApp = SQLAlchemy.init_app  # pragma: no cover


def _idempotent_init_app(self, app, **kwargs):  # type: ignore
    """A thin wrapper that ignores duplicate-registration RuntimeErrors."""
    try:
        _OriginalSQLAlchemyInitApp(self, app, **kwargs)
    except RuntimeError as exc:  # Duplicate registration throws RuntimeError
        msg = str(exc)
        duplicate_msg = "already been registered on this Flask app"
        if duplicate_msg in msg:
            # App already initialised – this is safe to ignore
            app.logger.debug("SQLAlchemy already initialised for this app; skipping redundant init_app call")
        else:
            raise


# Monkey-patch the method only once at import time
SQLAlchemy.init_app = _idempotent_init_app

# Create the global database instance AFTER the patch so it inherits behaviour
db = SQLAlchemy()


class BaseModel(db.Model):
    """Base model class with common fields and methods"""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def save(self):
        """Save the current instance to the database"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Delete the current instance from the database"""
        db.session.delete(self)
        db.session.commit()
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns} 