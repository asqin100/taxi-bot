"""Where to go usage tracking model."""
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, Date
from bot.database.db import Base


class WhereToGoUsage(Base):
    """Track 'Where to go' feature usage per user per day."""
    __tablename__ = "where_to_go_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    date = Column(Date, nullable=False, default=datetime.now().date)
    usage_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<WhereToGoUsage(user_id={self.user_id}, date={self.date}, count={self.usage_count})>"
