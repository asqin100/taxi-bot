"""AI Usage tracking model."""
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, Date
from bot.database.db import Base


class AIUsage(Base):
    """Track AI advisor usage per user per day."""
    __tablename__ = "ai_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    date = Column(Date, nullable=False, default=datetime.now().date)
    question_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<AIUsage(user_id={self.user_id}, date={self.date}, count={self.question_count})>"
