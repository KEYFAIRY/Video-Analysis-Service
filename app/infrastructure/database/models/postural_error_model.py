from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class PosturalErrorModel(Base):
    __tablename__ = "PosturalError"

    id = Column(Integer, primary_key=True, autoincrement=True)
    min_sec_init = Column(String(50), nullable=False)
    min_sec_end = Column(String(50), nullable=False)    
    explication = Column(String(500), nullable=True)
    id_practice = Column(Integer, nullable=False)