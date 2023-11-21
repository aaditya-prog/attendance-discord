import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

load_dotenv()

intents = discord.Intents.all()
intents.messages = True

bot = commands.Bot(command_prefix='/', intents=intents)

# SQLAlchemy setup
engine = create_engine('sqlite:///attendance_database.db', echo=True)
Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    name = Column(String)
    attendance = relationship("Attendance", back_populates="user")

class Attendance(Base):
    __tablename__ = 'attendance'
    attendance_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    check_in_time = Column(DateTime, default=datetime.now)
    check_out_time = Column(DateTime)
    remarks = Column(String)
    date = Column(Date)
    location = Column(String)  # Add the location field

    user = relationship("Users", back_populates="attendance")


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

# Function to provide command autocompletion for locations
async def location_completer(ctx, argument, command):
    # Your logic to suggest locations, for instance:
    locations = ['Location1', 'Location2', 'Location3']
    return [loc for loc in locations if loc.startswith(argument)]

@bot.command()
async def checkin(ctx, location: str, *, remarks="No remarks provided"):
    """Check-in to mark attendance at a specific location."""
    if ctx.guild and ctx.channel.name == 'attendance':
        # Get or create the user in the database
        user = session.query(Users).filter_by(username=ctx.author.name).first()

        if not user:
            # If the user doesn't exist, create a new user
            user = Users(username=ctx.author.name, name=str(ctx.author))  # Storing the user's name
            session.add(user)
            session.commit()

        # Check if the user has already checked in on the current date at the specified location
        existing_checkin = session.query(Attendance).filter_by(user_id=user.user_id, date=datetime.now().date(), location=location).first()

        if existing_checkin:
            await ctx.send(f"{ctx.author.mention}, you have already checked-in today at {location}!")
        else:
            new_attendance = Attendance(user_id=user.user_id, remarks=remarks, date=datetime.now().date(), location=location)
            session.add(new_attendance)
            session.commit()

            await ctx.send(f"{ctx.author.mention}, you have checked-in successfully at {location}!")
        checkin.completion = location_completer

@bot.command()
async def checkout(ctx, location: str, *, remarks="No remarks provided"):
    if ctx.guild and ctx.channel.name == 'attendance':
        # Get the user from the database (replace with your logic)
        user = session.query(Users).filter_by(username=ctx.author.name).first()

        if user:
            # Fetch the last check-in record for the user at the specified location
            last_checkin = session.query(Attendance).filter_by(user_id=user.user_id, location=location).order_by(Attendance.attendance_id.desc()).first()

            if last_checkin:
                if last_checkin.check_out_time:
                    await ctx.send(f"{ctx.author.mention}, you have already checked-out at {location}!")
                else:
                    last_checkin.check_out_time = datetime.now()
                    last_checkin.remarks = remarks
                    session.commit()

                    await ctx.send(f"{ctx.author.mention}, you have checked-out successfully from {location}!")
            else:
                await ctx.send(f"{ctx.author.mention}, you haven't checked-in yet at {location}!")
        else:
            # If the user doesn't exist, create a new user
            new_user = Users(username=ctx.author.name, name=str(ctx.author))  # Storing the user's name
            session.add(new_user)
            session.commit()

            await ctx.send(f"{ctx.author.mention}, you haven't checked-in yet! But we've registered your attendance.")


bot.run(os.getenv('BOT_TOKEN'))
