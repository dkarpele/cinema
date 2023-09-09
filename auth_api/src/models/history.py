import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from db.postgres import Base


class LoginHistory(Base):
    __tablename__ = 'logins_history'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    user_id = Column(UUID,
                     ForeignKey('users.id', ondelete='CASCADE'),
                     nullable=False)
    source = Column(String(255), default=None)
    login_time = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship('User', back_populates='login_histories')

    def __init__(self,
                 user_id: UUID,
                 source: str = None) -> None:
        self.user_id = user_id
        self.source = source
        self.login_time = self.login_time
