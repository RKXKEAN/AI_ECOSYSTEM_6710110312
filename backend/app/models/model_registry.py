from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_by = Column(String, nullable=False)
    dataset_used = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    versions = relationship("ModelVersion", back_populates="model", cascade="all, delete-orphan")

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    version = Column(String, nullable=False)
    metrics = Column(JSON, nullable=False, default=dict)
    storage_path = Column(String, nullable=False)
    is_deployed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    model = relationship("Model", back_populates="versions")
