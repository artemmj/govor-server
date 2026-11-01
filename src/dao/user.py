import uuid
from typing import Optional, Tuple, List, Dict

from sqlalchemy import select, exists, func, or_

from dao.base import BaseDAO
from models.user import User

from dependencies.db import DBDependency


class UserDAO(BaseDAO[User]):
    model = User

    def __init__(self, db: DBDependency):
        super().__init__(db)

    def _mapping_user_fields(self, user: User) -> Dict:
        return {
            "id": user.id,
            "email": user.email,
            "phone": user.phone,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "is_banned": user.is_banned,
            "is_verified": user.is_verified,
            "password_hash": user.password_hash,
        }

    async def check_uniques(self, phone: str, email: str | None) -> bool:
        async with self.db.read_only_scope() as session:
            conditions = [self.model.phone == phone]
            if email:
                conditions.append(self.model.email == email)
            stmt = select(exists().where(or_(*conditions)))
            result = await session.execute(stmt)
            return bool(result.scalar())

    async def check_uniques_excluding_user(
        self, phone: str | None, email: str | None, exclude_user_id: uuid.UUID
    ) -> bool:
        async with self.db.read_only_scope() as session:
            conditions = []
            if phone is not None:
                conditions.append(self.model.phone == phone)
            if email is not None and email.strip():
                conditions.append(self.model.email == email)
            if not conditions:
                return False
            stmt = select(
                exists().where(self.model.id != exclude_user_id, or_(*conditions))
            )
            result = await session.execute(stmt)
            return result.scalar()

    async def get_by_email_or_phone(self, email: str) -> Optional[Dict]:
        async with self.db.session_scope() as session:
            result = await session.execute(
                select(self.model).where(self.model.email == email)
            )
            user = result.scalar_one_or_none()
            if not user:
                return None
            return self._mapping_user_fields(user)

    async def get_by_phone(self, phone: str) -> Optional[Dict]:
        async with self.db.session_scope() as session:
            result = await session.execute(
                select(self.model).where(self.model.phone == phone)
            )
            user = result.scalar_one_or_none()
            if not user:
                return None
            return self._mapping_user_fields(user)

    async def get_paginated_list(
        self, page: int, per_page: int, search: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        async with self.db.read_only_scope() as session:
            query = select(self.model)
            count_query = select(func.count(self.model.id))

            if search:
                pattern = f"%{search}%"
                filter_cond = or_(
                    self.model.email.ilike(pattern),
                    self.model.phone.ilike(pattern),
                )
                query = query.where(filter_cond)
                count_query = count_query.where(filter_cond)

            total = (await session.execute(count_query)).scalar_one()

            result = await session.execute(
                query.order_by(self.model.created_at)
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
            users = result.scalars().unique().all()

            items = [self._mapping_user_fields(user) for user in users]
            return items, total
