import os
from datetime import datetime, timedelta
from typing import Optional

import discord
from discord import app_commands
from dotenv import load_dotenv

from db_settings import Attendance, Users, session

MY_GUILD = discord.Object(id=1117094425143820359)  # replace with your guild id

ALLOWED_LOCATIONS = ["Office", "Remote"]  # List of allowed locations


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # Here, we just synchronize the app commands to one guild(server).
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


intents = discord.Intents.default()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")


@client.tree.command()
@app_commands.describe(location="Specify the clock-in location")
async def clockin(interaction: discord.Interaction, location: str):
    """Marks your attendance"""
    if interaction.guild and interaction.channel.name == "attendance":
        user = session.query(Users).filter_by(user_id=interaction.user.id).first()

        if not user:
            user_name = interaction.user.nick or str(
                interaction.user
            )  # Using nickname where possible
            user = Users(user_id=interaction.user.id, name=user_name)
            session.add(user)
            session.commit()

        if location.capitalize() in ALLOWED_LOCATIONS:
            existing_checkin = (
                session.query(Attendance)
                .filter_by(
                    user_id=user.user_id,
                    date=datetime.now().date(),
                    check_out_time=None,
                )
                .first()
            )

            if existing_checkin:
                await interaction.response.send_message(
                    f"You have already clocked-in today!", ephemeral=True
                )
            else:
                location_text = (
                    "remote" if location.capitalize() == "Remote" else location.lower()
                )
                await interaction.response.send_message(
                    f"Success, have a great time at work.", ephemeral=True
                )

                check_in_time = datetime.now()
                new_attendance = Attendance(
                    user_id=user.user_id,
                    date=check_in_time.date(),
                    location=location.capitalize(),
                    check_in_time=check_in_time,
                )
                session.add(new_attendance)
                session.commit()
        else:
            await interaction.response.send_message(
                f"Please provide a valid location: {', '.join(ALLOWED_LOCATIONS)}",
                ephemeral=True,
            )
    else:
        await interaction.response.send_message(
            f"Please use the right channel #attendance for your attendances.",
            ephemeral=True,
        )


@client.tree.command()
@app_commands.describe(remarks="A short description of what you worked on today")
async def clockout(interaction: discord.Interaction, remarks: str):
    """Clock-out to mark the end of work."""
    if interaction.guild and interaction.channel.name == "attendance":
        user = session.query(Users).filter_by(user_id=interaction.user.id).first()

        if user:
            last_checkin = (
                session.query(Attendance)
                .filter_by(user_id=user.user_id, check_out_time=None)
                .order_by(Attendance.attendance_id.desc())
                .first()
            )

            if last_checkin:
                last_checkin.check_out_time = datetime.now()
                last_checkin.remarks = remarks

                hours_worked = last_checkin.check_out_time - last_checkin.check_in_time
                last_checkin.hours_worked = round(
                    hours_worked.total_seconds() / 3600, 2
                )

                session.commit()

                await interaction.response.send_message(
                    f"{interaction.user.mention}, you have clocked-out successfully. Working Hours: {last_checkin.hours_worked}",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, you haven't clocked-in yet!",
                    ephemeral=True,
                )
        else:
            user_name = interaction.user.nick or str(
                interaction.user
            )  # Using nickname where possible
            user = Users(user_id=interaction.user.id, name=user_name)
            session.add(user)
            session.commit()

            await interaction.response.send_message(
                f"{interaction.user.mention}, you haven't clocked-in yet! But we've registered your attendance.",
                ephemeral=True,
            )
    else:
        await interaction.response.send_message(
            f"Please use the right channel #attendance for your clockouts.",
            ephemeral=True,
        )


load_dotenv()
token = os.getenv("BOT_TOKEN_SECRET")
client.run(token)
