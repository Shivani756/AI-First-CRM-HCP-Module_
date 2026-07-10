from sqlalchemy import Column, Integer, String
from ..database import Base


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    type = Column(String(50))
    url = Column(String(500))
