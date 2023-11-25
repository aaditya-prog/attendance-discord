import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

url = "sqlite:///attendance_database.db"

# SQLAlchemy setup
engine = create_engine(url, echo=True)
Base = declarative_base()


class Users(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    name = Column(String)
    attendance = relationship("Attendance", back_populates="user")


class Attendance(Base):
    __tablename__ = "attendance"
    attendance_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    check_in_time = Column(DateTime, default=datetime.now)
    check_out_time = Column(DateTime)
    hours_worked = Column(String)
    remarks = Column(String)
    date = Column(Date)
    location = Column(String)  # Add the location field

    user = relationship("Users", back_populates="attendance")


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
