from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
