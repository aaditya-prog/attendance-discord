import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from db_settings import session, Users, Attendance
from datetime import datetime, timedelta

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='/', intents=intents)

ALLOWED_LOCATIONS = ["Office", "Remote"]  # List of allowed locations

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=1117094425143820359)
        await self.tree.sync(guild=1117094425143820359)

@bot.tree.command(name="hello")
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')


@bot.command(name="clockin", description="Command for clocking in")
async def clockin(ctx, location: str = None):
    """Clock-in to mark attendance."""
    if ctx.guild and ctx.channel.name == 'attendance':
        if not location:
            await ctx.send(f"{ctx.author.mention}, please include the location. Usage: `/clockin <Location>`")
            return
        
        member = ctx.guild.get_member(ctx.author.id)
        if member:
            user_name = member.nick or str(ctx.author)  # Using nickname if available, else using username
            user = session.query(Users).filter_by(user_id=ctx.author.id).first()

            if not user:
                user = Users(user_id=ctx.author.id, name=user_name)
                session.add(user)
                session.commit()

            if location.capitalize() in ALLOWED_LOCATIONS:
                existing_checkin = session.query(Attendance).filter_by(user_id=user.user_id, date=datetime.now().date(), check_out_time=None).first()

                if existing_checkin:
                    await ctx.send(f"{ctx.author.mention}, you have already clocked-in today!")
                else:
                    location_text = "remote" if location.capitalize() == "Remote" else location.lower()
                    await ctx.send(f"{ctx.author.mention}, you have clocked-in successfully at {location_text}!")

                    check_in_time = datetime.now()
                    new_attendance = Attendance(user_id=user.user_id, date=check_in_time.date(), location=location.capitalize(), check_in_time=check_in_time)
                    session.add(new_attendance)
                    session.commit()
            else:
                await ctx.send(f"{ctx.author.mention}, please provide a valid location: {', '.join(ALLOWED_LOCATIONS)}")

@bot.command(name="clockout", description="Command for clocking out")
async def clockout(ctx, *, remarks: str = "No remarks provided"):
    """Clock-out to mark the end of work."""
    if ctx.guild and ctx.channel.name == 'attendance':
        member = ctx.guild.get_member(ctx.author.id)
        if member:
            user_name = member.nick or str(ctx.author)  # Using nickname if available, else using username
            user = session.query(Users).filter_by(user_id=ctx.author.id).first()

            if user:
                last_checkin = session.query(Attendance).filter_by(user_id=user.user_id, check_out_time=None).order_by(Attendance.attendance_id.desc()).first()

                if last_checkin:
                    last_checkin.check_out_time = datetime.now()
                    last_checkin.remarks = remarks

                    hours_worked = last_checkin.check_out_time - last_checkin.check_in_time
                    last_checkin.hours_worked = round(hours_worked.total_seconds() / 3600, 2)
                    
                    session.commit()

                    await ctx.send(f"{ctx.author.mention}, you have clocked-out successfully with remarks: {remarks}! Hours: {last_checkin.hours_worked} hours")
                else:
                    await ctx.send(f"{ctx.author.mention}, you haven't clocked-in yet!")
            else:
                user = Users(user_id=ctx.author.id, name=user_name)
                session.add(user)
                session.commit()

                await ctx.send(f"{ctx.author.mention}, you haven't clocked-in yet! But we've registered your attendance.")



load_dotenv()
token = os.getenv('BOT_TOKEN_SECRET')
bot.run(token)
