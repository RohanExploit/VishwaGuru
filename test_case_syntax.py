from sqlalchemy import case, Column, Integer, String, create_engine, func
from sqlalchemy.orm import declarative_base, Session

Base = declarative_base()
class TestModel(Base):
    __tablename__ = 'test'
    id = Column(Integer, primary_key=True)
    status = Column(String)

engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
session = Session(engine)

session.add(TestModel(status='resolved'))
session.add(TestModel(status='open'))
session.commit()

print("Testing case((cond, 1), else_=0):")
try:
    q1 = session.query(func.sum(case((TestModel.status == 'resolved', 1), else_=0))).scalar()
    print(f"Result 1: {q1}")
except Exception as e:
    print(f"Error 1: {e}")

print("\nTesting case([(cond, 1)], else_=0):")
try:
    q2 = session.query(func.sum(case([(TestModel.status == 'resolved', 1)], else_=0))).scalar()
    print(f"Result 2: {q2}")
except Exception as e:
    print(f"Error 2: {e}")

print("\nTesting case({cond: 1}, else_=0):")
try:
    q3 = session.query(func.sum(case({TestModel.status == 'resolved': 1}, else_=0))).scalar()
    print(f"Result 3: {q3}")
except Exception as e:
    print(f"Error 3: {e}")
