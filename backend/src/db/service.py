from typing import TypeVar

from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.sql.expression import Select, SelectOfScalar

from src.utils.classes import singleton
from src.utils.env import env

T = TypeVar("T", bound=SQLModel)


@singleton
class DatabaseService:
    def __init__(self):
        self.engine = create_async_engine(env.DB_URL, pool_pre_ping=True)

    async def create_db_and_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def get_session(self) -> AsyncSession:
        async_session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        return async_session()

    async def get_first_in(self, clause: SelectOfScalar[T] | Select[T], session: AsyncSession | None = None) -> T | None:
        if session:
            result = await session.execute(clause)
            if isinstance(clause, SelectOfScalar):
                row: T | None = result.scalars().first()  # pyright: ignore[reportRedeclaration]
            else:
                row: T | None = result.first()  # type: ignore
            return row
        else:
            async with await self.get_session() as session:
                return await self.get_first_in(clause, session)

    async def get_first_in_or_throw(self, clause: SelectOfScalar[T] | Select[T], session: AsyncSession | None = None) -> T:
        if row := await self.get_first_in(clause, session):
            return row
        else:
            raise Exception("Row not found in database")

    async def get_all_in(self, clause: SelectOfScalar[T] | Select[T], session: AsyncSession | None = None) -> list[T]:
        if session:
            result = await session.execute(clause)
            if isinstance(clause, SelectOfScalar):
                rows: list[T] = result.scalars().all()  # type: ignore
            else:
                rows: list[T] = result.all()  # type: ignore
            return rows
        else:
            async with await self.get_session() as session:
                return await self.get_all_in(clause, session)

    async def add(self, obj: SQLModel, session: AsyncSession | None = None):
        """Adds an object to the database and commits the transaction immediately."""
        if session:
            session.add(obj)
            await session.commit()
            # Ensure server defaults (e.g., timestamps) are populated on the object
            await session.refresh(obj)
        else:
            async with await self.get_session() as session:
                await self.add(obj, session)

    async def insert_if_not_exists(self, obj: SQLModel, session: AsyncSession | None = None, commit: bool = True) -> bool:
        """
        Inserts the provided record if a row with the same primary key(s) already exists
        in the table then do nothing. Returns True if the record was inserted, False if it
        already existed. Does not commit; caller controls the transaction.

        IMPORTANT: The `obj` will not be part of the session after this call and should be fetched again from the database for modifications
        """
        if session:
            statement = postgresql.insert(obj.__class__).values(**obj.model_dump(exclude_unset=True)).on_conflict_do_nothing()
            result = await session.execute(statement)
            was_inserted = result.rowcount > 0

            if commit:
                await session.commit()

            return was_inserted

        else:
            async with await self.get_session() as session:
                return await self.insert_if_not_exists(obj, session, commit=commit)
