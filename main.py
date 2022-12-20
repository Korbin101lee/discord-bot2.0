import discord
import os
from discord.ext import commands
import asyncio
import sqlite3
import aiosqlite
import logging
import traceback
import logging.handlers
from discord.ext import commands
import sys
import traceback



logging.basicConfig(filename="bot.log", level=logging.DEBUG, filemode="a")


TOKEN = "ODMxOTY5NzE0MDAyNzIyODE2.YHc-LQ.msEMnZmXuLxgEkwbh2tunzqjJwQ"
PATH_TO_FILE = 'db_build.sql'
intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix='+', intents=intents)




@bot.event
async def on_command_error(ctx, error):
        """The event triggered when an error is raised while invoking a command.
        Parameters
        ------------
        ctx: commands.Context
            The context used for command invocation.
        error: commands.CommandError
            The Exception raised.
        """

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = (commands.CommandNotFound, )

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.send(f'{ctx.command} has been disabled.')

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
            except discord.HTTPException:
                pass

        # For this error example we check to see where it came from...
        elif isinstance(error, commands.BadArgument):
            if ctx.command.qualified_name == 'tag list':  # Check if the command being invoked is 'tag list'
                await ctx.send('I could not find that member. Please try again.')

        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


@bot.command()
async def load(ctx, extension):
    await bot.load_extension(f'cogs.{extension}')


@bot.command()
async def unload(ctx, extension):
    await bot.unload_extension(f'cogs.{extension}')


async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            # cut off the .py from the file name
            await bot.load_extension(f"cogs.{filename[:-3]}")

@bot.event
async def on_error(ctx, event, *args, **kwargs):
    message = args[0] #Gets the message object
    logging.warning(traceback.format_exc()) #logs the error
    await bot.send_message(message.channel, "You caused an error!") #send the message to the channel
    print("You caused an error!")

@bot.event
async def on_ready():
    print('Bot is online.')
    async with aiosqlite.connect("main.db") as db:
        async with db.cursor() as cursor:
            for line in open(PATH_TO_FILE).read().split(';\n'):
                await cursor.execute(line)
        await db.commit()


async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

asyncio.run(main())

