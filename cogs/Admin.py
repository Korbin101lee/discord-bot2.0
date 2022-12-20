import discord
from discord.ext import commands
import datetime
import sqlite3
import aiosqlite
from datetime import datetime
from discord.ext.commands import Cog, Greedy, Converter
from discord import Embed, Member, NotFound, Object
from typing import Optional

today = datetime.now()
#print('Today Datetime:', today)

iso_date = today.isoformat()
#print('ISO DateTime:', iso_date)

#format = today.fromisoformat(iso_date)
#print('format:', format)

#completeformat = format.strftime("%b %d %Y")
#print('completeformat:', completeformat)

#alueError: time data '2022-12-14T13:43:22.618788' does not match format 

class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief = "Deletes a warning from a Member", help = "!delWarn @User", aliases=["Delwarn","delwarn","DelWarn"])
    async def delWarn(self, ctx, Member: discord.User, warnNumber):
        if ctx.message.author.guild_permissions.manage_messages:
            async with aiosqlite.connect(r"C:\Users\joemo\OneDrive\Desktop\Projects\Discord Bot\main.db") as db:
                query = f"DELETE FROM logs WHERE LogId = {warnNumber};"
                await db.execute(query)
                await db.commit()

    @commands.command(brief = "Mutes a Member from the Guild", help = "!mute @User", aliases=["Mute"])
    async def mute(self, ctx, user: discord.User):
        if ctx.message.author.guild_permissions.deafen_members:
            embed=discord.Embed(description=f"<:ballot_box_with_check:1052800041041010758> {user.name}#{user.discriminator} was muted.", color=0x0f3fff)
            await ctx.send(embed=embed)
            await user.edit(mute=True)

    @commands.command(brief = "Unmutes a Member from the Guild", help = "!unmute @User", aliases=["Unmutes", "UnMutes","unMutes"])
    async def unmute(self, ctx, user: discord.User):
        if ctx.message.author.guild_permissions.deafen_members:
            embed=discord.Embed(description=f"<:ballot_box_with_check:1052800041041010758> {user.name}#{user.discriminator} was unmuted.", color=0x0f3fff)
            await ctx.send(embed=embed)
            await user.edit(mute=False)

    @commands.command(brief = "Deafens a Member from the Guild", help = "!deafen @User", aliases=["Deafen"])
    async def deafen(self, ctx, user: discord.User):
        if ctx.message.author.guild_permissions.deafen_members:
            embed=discord.Embed(description=f"<:ballot_box_with_check:1052800041041010758> {user.name}#{user.discriminator} was deafened.", color=0x0f3fff)
            await ctx.send(embed=embed)
            await user.edit(deafen=True)

    @commands.command(brief = "UnDeafens a Member from the Guild", help = "!Undeafen @User", aliases=["Undeafen", "UnDeafen", "unDeafen"])
    async def undeafen(self, ctx, user: discord.User):
        if ctx.message.author.guild_permissions.deafen_members:
            embed=discord.Embed(description=f"<:ballot_box_with_check:1052800041041010758> {user.name}#{user.discriminator} was undeafened.", color=0x0f3fff)
            await ctx.send(embed=embed)
            await user.edit(deafen=False)

    @commands.command(brief = "Purges Messages from the guild", help = "!purge @User", aliases=["purge","Purge"])
    @commands.bot_has_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    async def clear_messages(self, ctx, targets:Greedy[Member], limit: Optional[int] = 1):
        def _check(message):
            return not len(targets) or message.author in targets
        if 0 < limit <= 100:
            async with ctx.channel.typing():
                await ctx.message.delete()
                deleted = await ctx.channel.purge(limit=limit, check=_check)

                await ctx.send(f"Delted {len(deleted):,} messages.", delete_after=5)

        else:
            await ctx.send("The limit provided is not within acceptable bounds.")


    @commands.command(brief = "Warnings a Member from the Guild has", help = "!Warning @User", aliases=["Warnings","Warning","warning"])
    async def warnings(self, ctx, Member: discord.User):
        if ctx.message.author.guild_permissions.manage_messages:
            count = 0
            embed=discord.Embed(color=0xfb00ff)
            embed.set_author(name=f"Warnings for {Member.name}#{Member.discriminator} ({Member.id})", icon_url=f"{Member.display_avatar}")
            async with aiosqlite.connect(r"C:\Users\joemo\OneDrive\Desktop\Projects\Discord Bot\main.db") as db:
                async with db.execute("SELECT ModeratorId, TypeOfWarn, Reason, TimeOfDay FROM logs WHERE UserID = ?", [Member.id]) as cursor:
                    async for row in cursor:
                        local_iso_date = row[3]
                        format = datetime.fromisoformat(local_iso_date)
                        completeformat = format.strftime("%b %d %Y")
                        count = count + 1
                        user = await self.bot.fetch_user(row[0])
                        embed.add_field(name=f"Moderator:{user}", value=f"*{row[1]}*: {row[2]} - {completeformat}", inline=False)
            embed.set_footer(text=f"Number of Warnings {count}")
            await ctx.send(embed=embed)

    @commands.command(brief = "Warns a Member from the Guild", help = "!Warn @User",  aliases=["Warn"])
    async def warn(self, ctx, Member: discord.User, *, reason=None):
        if ctx.message.author.guild_permissions.manage_messages:
            await ctx.send(f"<@{Member.id}> has been warned for {reason}")
            channel = self.bot.get_channel(883145817576333342)
            embed=discord.Embed(title="Member Warned", color=0xfb00ff)
            embed.set_thumbnail(url=f"{Member.display_avatar}")
            embed.add_field(name="Member", value=f"<@{Member.id}>", inline=False)
            embed.add_field(name="Warned By", value=f"<@{ctx.message.author.id}>", inline=False)
            embed.add_field(name="Reason", value=f"{reason}", inline=False)
            embed.timestamp = datetime.utcnow()
            embed.set_footer(text=f"ID: {Member.id}",icon_url="https://i.imgur.com/uZIlRnK.png")
            await channel.send(embed=embed)
            async with aiosqlite.connect(r"C:\Users\joemo\OneDrive\Desktop\Projects\Discord Bot\main.db") as db:
                query = "INSERT INTO logs (GuildID, UserID, ModeratorId, TypeOfWarn, Reason, TimeOfDay) VALUES (?, ?, ?, ?, ?, ?)"
                params = ctx.guild.id, Member.id, ctx.message.author.id ,"Warning", reason, iso_date
                await db.execute(query , params)
                await db.commit()
        else:
            await ctx.send("You do not have permission to use this command")




    @commands.command(brief = "Kicks a Member from the Guild", help = ".Kick @User")
    async def kick(self, ctx, Member: discord.User, *, reason=None, aliases=["Kick"]):
        if ctx.message.author.guild_permissions.kick_members:
            await ctx.send(f"<@{Member.id}> has been kicked for {reason}")
            await Member.kick()
            channel = self.bot.get_channel(883145817576333342)
            embed=discord.Embed(title="Member Kicked", color=0xfb00ff)
            embed.set_thumbnail(url=f"{Member.display_avatar}")
            embed.add_field(name="Member", value=f"<@{Member.id}>", inline=False)
            embed.add_field(name="Kicked By", value=f"<@{ctx.message.author.id}>", inline=False)
            embed.add_field(name="Reason", value=f"{reason}", inline=False)
            embed.timestamp = datetime.utcnow()
            embed.set_footer(text=f"ID: {Member.id}",icon_url="https://i.imgur.com/uZIlRnK.png")
            await channel.send(embed=embed)
            async with aiosqlite.connect(r"C:\Users\joemo\OneDrive\Desktop\Projects\Discord Bot\main.db") as db:
                query = "INSERT INTO logs (GuildID, UserID, ModeratorId, TypeOfWarn, Reason, TimeOfDay) VALUES (?, ?, ?, ?, ?, ?)"
                params = ctx.guild.id, Member.id, ctx.message.author.id ,"Kicked", reason, iso_date
                await db.execute(query , params)
                await db.commit()            
        else:
            await ctx.send("You do not have permission to use this command")


    @commands.command(brief = "Bans a Member from the Guild", help = ".Kick @User", aliases=["Ban"])
    async def ban(self, ctx, Member: discord.User, *, reason=None):
        if ctx.message.author.guild_permissions.ban_members:
            await ctx.send(f"<@{Member.id}> has been banned for {reason}")
            await ctx.guild.ban(Member)
            channel = self.bot.get_channel(883145817576333342)
            embed=discord.Embed(title="Member Banned", color=0xfb00ff)
            embed.set_thumbnail(url=f"{Member.display_avatar}")
            embed.add_field(name="Member", value=f"<@{Member.id}>", inline=False)
            embed.add_field(name="Banned By", value=f"<@{ctx.message.author.id}>", inline=False)
            embed.add_field(name="Reason", value=f"{reason}", inline=False)
            embed.timestamp = datetime.utcnow()
            embed.set_footer(text=f"ID: {Member.id}",icon_url="https://i.imgur.com/uZIlRnK.png")
            await channel.send(embed=embed)
            async with aiosqlite.connect(r"C:\Users\joemo\OneDrive\Desktop\Projects\Discord Bot\main.db") as db:
                query = "INSERT INTO logs (GuildID, UserID, ModeratorId, TypeOfWarn, Reason, TimeOfDay) VALUES (?, ?, ?, ?, ?, ?)"
                params = ctx.guild.id, Member.id, ctx.message.author.id ,"Banned", reason, iso_date
                await db.execute(query , params)
                await db.commit()            
        else:
            await ctx.send("You do not have permission to use this command")

    @commands.command(brief = "Unbans a Member from the Guild", help = ".Kick @User", aliases=["UnBan"])
    async def unban(self, ctx, Member: discord.User):
        if ctx.message.author.guild_permissions.ban_members:
            await ctx.send(f"<@{Member.id}> has been unbanned")
            await ctx.guild.unban(Member)
            channel = self.bot.get_channel(883145817576333342)
        else:
            await ctx.send("You do not have permission to use this command")


async def setup(bot):
    await bot.add_cog(Admin(bot))