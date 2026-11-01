# from typing import TYPE_CHECKING
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column  # , relationship

from models import Base, FullMixin

# if TYPE_CHECKING:
#     from models import ChatMessage, ChatMembership


class User(Base, FullMixin):
    phone: Mapped[str] = mapped_column(
        String(15), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(127), unique=True, nullable=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # roles: Mapped[list[Role]] = relationship(
    #     secondary="user_roles",
    #     back_populates="users",
    #     lazy="selectin",
    # )

    # memberships: Mapped[list["ChatMembership"]] = relationship(
    #     back_populates="user", cascade="all, delete-orphan"
    # )
    # messages: Mapped[list["ChatMessage"]] = relationship(
    #     back_populates="sender", cascade="all, delete-orphan"
    # )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, email={self.email})"
