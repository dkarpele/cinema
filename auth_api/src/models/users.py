import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Boolean, ForeignKey, \
    UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from passlib.context import CryptContext

from db.postgres import Base
from models.history import LoginHistory


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    disabled = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    social_accounts = relationship('SocialAccount', back_populates='users')
    login_histories = relationship('LoginHistory', back_populates='users')

    def __init__(self,
                 email: str,
                 password: str,
                 first_name: str = None,
                 last_name: str = None,
                 disabled: bool = False,
                 is_admin: bool = False) -> None:
        self.email = email
        self.password = pwd_context.hash(password)
        self.first_name = first_name if first_name else ""
        self.last_name = last_name if last_name else ""
        self.disabled = disabled
        self.is_admin = is_admin

    def __repr__(self) -> str:
        return f'<User {self.email}>'


class SocialAccount(Base):
    __tablename__ = 'social_account'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    user_id = Column(UUID,
                     ForeignKey('users.id', ondelete='CASCADE'),
                     nullable=False)
    social_id = Column(String, nullable=False)
    social_name = Column(String(50), nullable=False)
    social_id_name_idx = UniqueConstraint('social_id', 'social_name',
                                          name='social_pk')

    users = relationship('User', back_populates="social_accounts")

    def __init__(self,
                 social_id: str,
                 social_name: str,
                 user_id: UUID):
        self.user_id = user_id
        self.social_id = social_id
        self.social_name = social_name

    def __repr__(self):
        return f'<SocialAccount {self.social_name}:{self.user_id}>'
