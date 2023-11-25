import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

import discord
from discord import app_commands
from dotenv import load_dotenv

from db_settings import Attendance, Users, session

MY_GUILD = discord.Object(id=1117094425143820359)  # replace with your guild id


class Location(Enum):
    REMOTE = "Remote"
    OFFICE = "Office"
    # Add other allowed locations here


class Bot(discord.Client):
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
client = Bot(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")


@client.event
async def on_member_join(member):
    guild = member.guild
    if guild.system_channel is not None:
        to_send = f"Welcome {member.mention} to {guild.name}!"
        await guild.system_channel.send(to_send)


@client.tree.command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f"Hi, {interaction.user.mention}")


@client.tree.command()
@app_commands.describe(
    first_value="The first value you want to add something to",
    second_value="The value you want to add to the first value",
)
async def add(interaction: discord.Interaction, first_value: int, second_value: int):
    """Adds two numbers together."""
    await interaction.response.send_message(
        f"{first_value} + {second_value} = {first_value + second_value}"
    )


@client.tree.command()
@app_commands.describe(location="Specify the clock-in location")
async def clockin(interaction: discord.Interaction, location: Location):
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

        existing_checkin = (
            session.query(Attendance)
            .filter_by(
                user_id=user.user_id, date=datetime.now().date(), check_out_time=None
            )
            .first()
        )

        if existing_checkin:
            await interaction.response.send_message(
                f"You have already clocked-in today!", ephemeral=True
            )
        else:
            location_text = (
                location.value.lower() if location != Location.REMOTE else "remote"
            )
            await interaction.response.send_message(
                f"Success, have a great time at work.", ephemeral=True
            )

            check_in_time = datetime.now()
            new_attendance = Attendance(
                user_id=user.user_id,
                date=check_in_time.date(),
                location=location.value.capitalize(),
                check_in_time=check_in_time,
            )
            session.add(new_attendance)
            session.commit()
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
                    f"Clocked-out successfully. Working Hours: {last_checkin.hours_worked}",
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


# The rename decorator allows us to change the display of the parameter on Discord.
# In this example, even though we use `text_to_send` in the code, the client will use `text` instead.
# Note that other decorators will still refer to it as `text_to_send` in the code.
@client.tree.command()
@app_commands.rename(text_to_send="text")
@app_commands.describe(text_to_send="Text to send in the current channel")
async def send(interaction: discord.Interaction, text_to_send: str):
    """Sends the text into the current channel."""
    await interaction.response.send_message(text_to_send)


# To make an argument optional, you can either give it a supported default argument
# or you can mark it as Optional from the typing standard library. This example does both.
@client.tree.command()
@app_commands.describe(
    member="The member you want to get the joined date from; defaults to the user who uses the command"
)
async def joined(
    interaction: discord.Interaction, member: Optional[discord.Member] = None
):
    """Says when a member joined."""
    # If no member is explicitly provided then we use the command user here
    member = member or interaction.user

    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(
        f"{member} joined {discord.utils.format_dt(member.joined_at)}"
    )


# A Context Menu command is an app command that can be run on a member or on a message by
# accessing a menu within the client, usually via right clicking.
# It always takes an interaction as its first parameter and a Member or Message as its second parameter.


# This context menu command only works on members
@client.tree.context_menu(name="Show Join Date")
async def show_join_date(interaction: discord.Interaction, member: discord.Member):
    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(
        f"{member} joined at {discord.utils.format_dt(member.joined_at)}"
    )


# This context menu command only works on messages
@client.tree.context_menu(name="Report to Moderators")
async def report_message(interaction: discord.Interaction, message: discord.Message):
    # We're sending this response message with ephemeral=True, so only the command executor can see it
    await interaction.response.send_message(
        f"Thanks for reporting this message by {message.author.mention} to our moderators.",
        ephemeral=True,
    )

    # Handle report by sending it into a log channel
    log_channel = interaction.guild.get_channel(0)  # replace with your channel id

    embed = discord.Embed(title="Reported Message")
    if message.content:
        embed.description = message.content

    embed.set_author(
        name=message.author.display_name, icon_url=message.author.display_avatar.url
    )
    embed.timestamp = message.created_at

    url_view = discord.ui.View()
    url_view.add_item(
        discord.ui.Button(
            label="Go to Message", style=discord.ButtonStyle.url, url=message.jump_url
        )
    )

    await log_channel.send(embed=embed, view=url_view)


load_dotenv()
token = os.getenv("BOT_TOKEN_SECRET")
client.run(token)
