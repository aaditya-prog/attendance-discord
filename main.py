import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from db_settings import session, Users, Attendance
from datetime import datetime

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.command(name="clockin", description="Command for clocking in")
async def clockin(ctx, location: str, *, remarks: str = "No remarks provided"):
    """Clock-in to mark attendance at a specific location."""
    if ctx.guild and ctx.channel.name == 'attendance':
        member = ctx.guild.get_member(ctx.author.id)
        if member:
            user_name = member.nick or str(ctx.author)  # Using nickname if available, else using username
            user = session.query(Users).filter_by(user_id=ctx.author.id).first()

            if not user:
                user = Users(user_id=ctx.author.id, name=user_name)
                session.add(user)
                session.commit()

            existing_checkin = session.query(Attendance).filter_by(user_id=user.user_id, date=datetime.now().date(), location=location).first()

            if existing_checkin:
                await ctx.send(f"{ctx.author.mention}, you have already clocked-in today at {location}!")
            else:
                new_attendance = Attendance(user_id=user.user_id, remarks=remarks, date=datetime.now().date(), location=location)
                session.add(new_attendance)
                session.commit()

                await ctx.send(f"{ctx.author.mention}, you have clocked-in successfully at {location}!")

@bot.command(name="clockout", description="Command for clocking out")
async def clockout(ctx, location: str, *, remarks: str = "No remarks provided"):
    if ctx.guild and ctx.channel.name == 'attendance':
        member = ctx.guild.get_member(ctx.author.id)
        if member:
            user_name = member.nick or str(ctx.author)  # Using nickname if available, else using username
            user = session.query(Users).filter_by(user_id=ctx.author.id).first()

            if user:
                last_checkin = session.query(Attendance).filter_by(user_id=user.user_id, location=location).order_by(Attendance.attendance_id.desc()).first()

                if last_checkin:
                    if last_checkin.check_out_time:
                        await ctx.send(f"{ctx.author.mention}, you have already clocked-out at {location}!")
                    else:
                        last_checkin.check_out_time = datetime.now()
                        last_checkin.remarks = remarks
                        session.commit()

                        await ctx.send(f"{ctx.author.mention}, you have clocked-out successfully from {location}!")
                else:
                    await ctx.send(f"{ctx.author.mention}, you haven't clocked-in yet at {location}!")
            else:
                user = Users(user_id=ctx.author.id, name=user_name)
                session.add(user)
                session.commit()

                await ctx.send(f"{ctx.author.mention}, you haven't clocked-in yet! But we've registered your attendance.")

load_dotenv()
token = os.getenv('BOT_TOKEN_SECRET')
bot.run(token)
