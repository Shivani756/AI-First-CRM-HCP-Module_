from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from ..database import Base


class HCP(Base):
    __tablename__ = "hcps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    specialty = Column(String(100))
    email = Column(String(200))
    phone = Column(String(50))
    organization = Column(String(200))

    interactions = relationship("Interaction", back_populates="hcp")
