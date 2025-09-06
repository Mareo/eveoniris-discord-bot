from __future__ import annotations

from sqlalchemy import URL, ForeignKey
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.ext.declarative import DeferredReflection
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    type_annotation_map = {list[str]: JSON}


class Reflected(DeferredReflection):
    __abstract__ = True


class User(Reflected, Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(unique=True)
    roles: Mapped[list[str]] = mapped_column()
    personnage_id: Mapped[int | None] = mapped_column(ForeignKey("personnage.id"))
    personnage: Mapped[Personnage | None] = relationship(
        "Personnage", foreign_keys=[personnage_id]
    )

    def __repr__(self):
        return f"<User: id={self.id}, email={self.email}>"


class Personnage(Reflected, Base):
    __tablename__ = "personnage"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column()
    user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"))
    user: Mapped[User | None] = relationship(User, foreign_keys=[user_id])
    vivant: Mapped[bool] = mapped_column()

    def __repr__(self):
        return f"<SecondaryGroup: id={self.id}, label={self.label}>"


class Membre(Reflected, Base):
    __tablename__ = "membre"


class SecondaryGroup(Reflected, Base):
    __tablename__ = "secondary_group"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column()
    members: Mapped[list[Personnage]] = relationship(Personnage, secondary="membre")

    def __repr__(self):
        return f"<SecondaryGroup: id={self.id}, label={self.label}>"


async def init_engine(
    host: str, port, user: str, password: str, database: str
) -> AsyncEngine:
    global engine
    engine = create_async_engine(
        URL.create(
            "mysql+aiomysql",
            host=host,
            port=port,
            username=user,
            password=password,
            database=database,
            query={
                "charset": "utf8mb4",
            },
        )
    )
    async with engine.connect() as connection:
        await connection.run_sync(lambda c: Reflected.prepare(c.engine))
    return engine
