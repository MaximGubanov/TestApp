import os

from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.ext.declarative import declarative_base

from creds import USER, PASSWORD, HOST, PORT, DATABASE


Base = declarative_base()
# engine = create_engine("postgresql+psycopg2://user:password@host_name:port/database_name")
engine = create_engine(f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}")


class GoogleSheetsData(Base):

    __tablename__ = 'test_table'

    no = Column(Integer, primary_key=True, nullable=False)
    order_no = Column(Integer, nullable=False)
    price_dollar = Column(Integer, nullable=False)
    price_rub = Column(Float, nullable=False)
    delivery_time = Column(String, nullable=False)


Base.metadata.create_all(engine)


if __name__ == '__main__':
    #  тест движка
    engine.connect()
    print(engine)

    #  удаление таблицы
    # Base.metadata.drop_all(engine)
