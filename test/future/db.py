from contextlib import contextmanager

from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import sessionmaker


pg_url = 'postgresql://{user}:{password}@{host}:{port}/{db_name}'.format(
    user=['PG_USERNAME'],
    password=['PG_PASSWORD'],
    host=['PG_HOST'],
    port=['PG_PORT'],
    db_name=['PG_DB_NAME'],
)

engine = create_engine(pg_url, echo=['SHOW_SQL'])

OurSession = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope():
    session = OurSession()

    try:
        yield session
        session.commit()
    except Exception as ex:
        session.rollback()
        raise ex
    finally:
        session.close()


def get_engine() -> Engine:
    return engine


async def create_tables_and_add_initial_data(eng: Engine):
    #Base.metadata.create_all(eng)

    with engine.connect() as conn:
        stmt: str = """INSERT INTO public.tgame_type (dfname_en, dfname) VALUES ('RANDOM', 'Игра со случайным соперником');
INSERT INTO public.tgame_type (dfname_en, dfname) VALUES ('FRIEND', 'Игра с другом');
INSERT INTO public.tgame_type (dfname_en, dfname) VALUES ('COMPUTER', 'Игра с компьютером');
--
INSERT INTO public.tplayer_state (dfname_en, dfname) VALUES ('SEARCHING_FOR_OPPONENT', 'Поиск соперника');
INSERT INTO public.tplayer_state (dfname_en, dfname) VALUES ('SHIPS_POSITIONING', 'Расстановка кораблей');
INSERT INTO public.tplayer_state (dfname_en, dfname) VALUES ('PLAYING', 'Игра');"""

        sql = text(stmt)
        conn.execute(sql)

        conn.commit()
