from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Tag


class TagService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tags(
        self,
        page: int = 1,
        page_size: int = 20,
        name: Optional[str] = None,
    ) -> dict:
        query = select(Tag)

        if name:
            query = query.where(Tag.name.ilike(f"%{name}%"))

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        query = query.order_by(Tag.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        tags = result.scalars().all()

        return {
            "success": True,
            "data": [
                {
                    "id": tag.id,
                    "name": tag.name,
                    "description": tag.description,
                    "created_at": tag.created_at.isoformat() if tag.created_at else None,
                    "updated_at": tag.updated_at.isoformat() if tag.updated_at else None,
                }
                for tag in tags
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        }

    async def get_all_tags(self) -> List[dict]:
        result = await self.db.execute(
            select(Tag).order_by(Tag.name)
        )
        tags = result.scalars().all()
        return [
            {
                "id": tag.id,
                "name": tag.name,
                "description": tag.description,
            }
            for tag in tags
        ]

    async def get_tag(self, tag_id: int) -> Optional[Tag]:
        result = await self.db.execute(
            select(Tag).where(Tag.id == tag_id)
        )
        return result.scalar_one_or_none()

    async def get_tag_by_name(self, name: str) -> Optional[Tag]:
        result = await self.db.execute(
            select(Tag).where(Tag.name == name)
        )
        return result.scalar_one_or_none()

    async def create_tag(
        self,
        name: str,
        description: Optional[str] = None,
    ) -> Optional[Tag]:
        existing = await self.get_tag_by_name(name)
        if existing:
            return None

        tag = Tag(
            name=name,
            description=description,
        )
        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)
        return tag

    async def update_tag(
        self,
        tag_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Tag]:
        tag = await self.get_tag(tag_id)
        if not tag:
            return None

        if name is not None:
            existing = await self.get_tag_by_name(name)
            if existing and existing.id != tag_id:
                return None
            tag.name = name

        if description is not None:
            tag.description = description

        await self.db.commit()
        await self.db.refresh(tag)
        return tag

    async def delete_tag(self, tag_id: int) -> bool:
        tag = await self.get_tag(tag_id)
        if not tag:
            return False

        await self.db.delete(tag)
        await self.db.commit()
        return True

    async def validate_tags_exist(self, tag_names: List[str]) -> bool:
        if not tag_names:
            return True

        result = await self.db.execute(
            select(Tag.name).where(Tag.name.in_(tag_names))
        )
        existing_tags = {row[0] for row in result.fetchall()}
        return all(tag in existing_tags for tag in tag_names)
