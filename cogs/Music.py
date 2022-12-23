import json
from datetime import datetime

import discord
import wavelink
from discord.ext import commands
from wavelink.ext import spotify
from discord import app_commands
from typing import Union


class CustomPlayer(wavelink.Player):

    def __init__(self):
        super().__init__()
        self.queue = wavelink.Queue()


class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        """Connect to our Lavalink nodes."""
        await self.bot.wait_until_ready()

        self.wavelink_node = await wavelink.NodePool.create_node(bot=self.bot,
                                            host='127.0.0.1',
                                            port=2333,
                                            password='youshallnotpass',
                                            identifier='TEST',
                                            region='us_west',
                                            spotify_client=spotify.SpotifyClient(client_id='970cde25be5741d59c346e1e8d0914d7', client_secret='fa982671f44c428b9721e5dd8c3191f8'))


    async def teardown(self):
        try:
            await self.destroy()
        except KeyError:
            pass

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.member.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        """_summary_
        Args:
            member (discord.member.Member): _description_
            before (discord.VoiceState): _description_
            after (discord.VoiceState): _description_
        """
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                voice_channel = self.bot.get_channel(before.channel.id)
                await voice_channel.send(
                    f"Disconnected on {discord.utils.format_dt(datetime.now())}."
                )
                await self.disconnect_player(self, self.bot, member.guild)

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("Pong!")
        
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Called when the Node you are connecting to has initialised and successfully connected to Lavalink."""
        print(f"Node {node.identifier} is ready!")

    @commands.Cog.listener()
    async def on_wavelink_websocket_closed(self, player: wavelink.Player, reason, code):
        """Called when the Node websocket has been closed by Lavalink."""
        print(f"websocket_closed {reason} code: {code}")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, player: wavelink.Player, track: wavelink.Track):
        """Called when a track starts playing."""
        print(f"Track {track.title} {track.author} Started Playing.")

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, player: wavelink.Player, track: wavelink.Track, error):
        """Called when a TrackException occurs in Lavalink."""
        print(f"TrackException has occured {track.title} {error}")

    @commands.Cog.listener()
    async def on_wavelink_track_stuck(self, player: wavelink.Player, track: wavelink.Track, threshold):
        """Called when a TrackStuck occurs in Lavalink."""
        print(f"TrackStuck has occured {track.title} {threshold}")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: CustomPlayer, track: wavelink.Track, reason):
        """Called when the current track has finished playing."""
        if not player.queue.is_empty:
            next_track = player.queue.get()
            await player.play(next_track)


    @commands.command(aliases=["join"])
    async def connect(self, ctx):
        vc = ctx.voice_client
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send("Please join a voice channel to connect.")

        if not vc:
            await ctx.author.voice.channel.connect(cls=CustomPlayer())
        else:
            await ctx.send("The bot is already connected to a voice channel")

    


    @commands.hybrid_command(name="play", with_app_command=True, aliases=["p"])
    async def play(self, ctx: commands.Context, *, search: str):
        """Play a song with the given search query.
        If not connected, connect to our voice channel.
        Args:
            ctx (commands.Context): _description_
            search (str): _description_
        """

        if not ctx.author.voice:
            await ctx.send("You are not connected to any voice channel.")
            return

        if ctx.voice_client:
            if ctx.voice_client.channel.id != ctx.author.voice.channel.id:
                await ctx.send("Bot is already playing in a voice channel.")
                return

        await ctx.send(f"{search}")

        # this is spotify playlist or album
        if (
            "https://open.spotify.com/playlist" in search
            or "https://open.spotify.com/album" in search
        ):
            # this is spotify playlist
            if not ctx.voice_client:
                vc: wavelink.Player = await ctx.author.voice.channel.connect(
                    cls=wavelink.Player, self_deaf=True
                )
                async for partial in spotify.SpotifyTrack.iterator(
                    query=search, partial_tracks=True
                ):
                    await self.add_spotify_track(ctx, partial)
            else:
                async for partial in spotify.SpotifyTrack.iterator(
                    query=search, partial_tracks=True
                ):
                    await self.add_track(ctx, partial)

        elif "https://www.youtube.com/playlist" in search:
            if not ctx.voice_client:
                vc: wavelink.Player = await ctx.author.voice.channel.connect(
                    cls=wavelink.Player
                )
                playlist = await vc.node.get_playlist(wavelink.YouTubePlaylist, search)
                # print(playlist.tracks)

                if len(playlist.tracks) == 1:
                    track = await vc.play(playlist.tracks[0])
                    await ctx.send(f"Now playing: {track.title}")
                else:
                    track = await vc.play(playlist.tracks[0])
                    await ctx.send(f"Now playing: {track.title}")
                    for track in playlist.tracks[1:]:
                        await self.add_track(ctx, track)
            else:
                vc: wavelink.Player = ctx.voice_client
                playlist = await vc.node.get_playlist(wavelink.YouTubePlaylist, search)
                for track in playlist.tracks:
                    await self.add_track(ctx, track)

        else:
            partial = wavelink.PartialTrack(query=search, cls=wavelink.YouTubeTrack)
            if not ctx.voice_client:
                vc: wavelink.Player = await ctx.author.voice.channel.connect(
                    cls=wavelink.Player
                )
                track = await vc.play(partial)
                await ctx.send(f"Now playingPlaying 🎶 {track.title} - Now!")
            else:
                await self.add_track(ctx, partial)         


    @commands.hybrid_command(name="skip", with_app_command=True, aliases=["s"])
    async def skip_command(self, ctx: commands.Context):
        """Skips currently playing song and play next song in queue.
        Args:
            ctx (commands.Context): _description_
        """
        if not ctx.author.voice:
            await ctx.send("You are not connected to any voice channel.")
            return

        vc: wavelink.Player = ctx.voice_client

        if vc is None:
            await ctx.send("Bot is not playing anything.")
            return
        if vc:
            if ctx.voice_client.channel.id != ctx.author.voice.channel.id:
                await ctx.send("Join VC the bot is playing in to use `skip`.")
                return

        if not vc.queue.is_empty:
            await vc.stop()
            await ctx.send(f"Now playing: {vc.queue[0].title}")


    async def add_track(
        self,
        ctx: commands.Context,
        track: Union[wavelink.PartialTrack, wavelink.YouTubeTrack],
    ):
        """_summary_
        Args:
            ctx (commands.Context): _description_
            track (Union[wavelink.PartialTrack, wavelink.YouTubeTrack]): _description_
        """
        if not track:
            await ctx.send("No tracks found.")
            return

        vc: wavelink.Player = ctx.voice_client
        await vc.queue.put_wait(track)

        #await ctx.send(f"Added {track.title} to the queue.", delete_after=20)

        if not vc.is_playing() and not vc.queue.is_empty:
            await ctx.send(f"Now playing: {track.title}")
            await vc.play(await vc.queue.get_wait())

    @commands.command()
    async def pause(self, ctx):
        """Pauses a song in the query"""
        vc = ctx.voice_client
        if vc:
            if vc.is_playing() and not vc.is_paused():
                await vc.pause()
            else:
                await ctx.send("Nothing is playing.")
        else:
            await ctx.send("The bot is not connected to a voice channel")

    @commands.command()
    async def resume(self, ctx):
        """Pauses a song in the query"""
        vc = ctx.voice_client
        if vc:
            if vc.is_paused():
                await vc.resume()
            else:
                await ctx.send("Nothing is paused.")
        else:
            await ctx.send("The bot is not connected to a voice channel")
      


    @commands.hybrid_command(name="queue", with_app_command=True, aliases=["q"])
    async def queue_command(self, ctx: commands.Context) -> None:
        if not ctx.author.voice:
            await ctx.send("You are not connected to any voice channel.")
            return

        vc: wavelink.Player = ctx.voice_client
        
        if vc is None:
            await ctx.send("Bot is not playing anything.")
            return

        if not vc.queue.is_empty:
            await ctx.send(embed=self.get_queue_embed(ctx))
        else:
            await ctx.send("Queue is empty.")    


    def get_queue_embed(self, ctx: commands.Context) -> discord.Embed:
        """_summary_
        Args:
            ctx (commands.Context): _description_
        Returns:
            discord.Embed: _description_
        """
        vc: wavelink.Player = ctx.voice_client

        embed = discord.Embed(
            title=f"**Queue for {ctx.guild.name}**",
            url="https://disboard.org/server/883145816158650449",
            colour=ctx.author.colour,
            timestamp=datetime.utcnow(),
        )


        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )


        if vc.track:
            embed.add_field(name=f"__Now Playing__", value=f"[{vc.track.title[0:1023]}]({vc.track.uri[0:1023]})", inline=False)

        value = ""
        for track in vc.queue:
            value += f"\n {track.title}"

        embed.add_field(
            name="Next up",
            value=value[0:1023],
            inline=False,
        )

        return embed

    @commands.hybrid_command(name="playing", with_app_command=True, aliases=["np"])
    async def playing_command(self, ctx: commands.Context) -> None:
        """Show currently playing song.
        Args:
            ctx (commands.Context): _description_
        """

        if not ctx.author.voice:
            await ctx.send("You are not connected to any voice channel.")
            return

        vc: wavelink.Player = ctx.voice_client

        if vc is None:
            await ctx.send("Bot is not playing anything.")
            return

        if not vc.is_playing or not vc.track:
            await ctx.send("Bot is not playing anything.")
        else:
            await ctx.send(embed=self.get_playing_embed(ctx))


    def get_playing_embed(self, ctx: commands.Context) -> discord.Embed:
        """Display info of currently playing audio.
        Args:
            ctx (commands.Context): _description_
        Returns:
            discord.Embed: _description_
        """

        vc: wavelink.Player = ctx.voice_client

        embed = discord.Embed(
            title="Now playing",
            colour=ctx.author.colour,
        )
        embed.set_author(name="Now Playing🎶", icon_url=f"{ctx.author.display_avatar}")
        
        embed.add_field(name="Track", value=f"[{vc.track.title}]({vc.track.uri})", inline=False)
        embed.add_field(
            name="Artist",
            value=vc.track.author if vc.track.author else "None",
            inline=False,
        )

        if isinstance(vc.track, wavelink.YouTubeTrack):
            embed.set_image(url=vc.track.thumbnail)

        

        position = divmod(vc.position, 60)
        length = divmod(vc.track.length, 60)
        embed.add_field(
            name=f"`{int(position[0])}:{round(position[1]):02}/{int(length[0])}:{round(length[1]):02}`",
            value="\u200b",
            inline=False
        )

        """embed.add_field(
            name=f"```Requested by:```",
            value="\u200b",
            inline=False,
        )"""

        return embed


    @commands.hybrid_command(name="disconnect", with_app_command=True)
    async def disconnect_command(self, ctx: commands.Context):
        """Disconnect bot
        Args:
            ctx (commands.Context): _description_
        """

        if not ctx.author.voice:
            await ctx.send("You are not connected to any voice channel.")
            return

        if ctx.voice_client.channel is None:
            await ctx.send("Bot is not playing anything.")
            return

        if ctx.voice_client.channel.id != ctx.author.voice.channel.id:
            await ctx.send(
                "Join the voice channel the bot is playing in to disconnect it."
            )
            return

        await self.disconnect_player(self, self.bot, ctx.guild)
        await ctx.send(
            f"Disconnected by {ctx.author.mention} on {discord.utils.format_dt(datetime.now())} ."
        )

    @commands.hybrid_command(name="clear", with_app_command=True)
    async def clear_command(self, ctx: commands.Context):
        if not ctx.author.voice:
            await ctx.send("You are not connected to any voice channel.")
            return

        if ctx.voice_client.channel is None:
            await ctx.send("Bot is not playing anything.")
            return

        if ctx.voice_client.channel.id != ctx.author.voice.channel.id:
            await ctx.send(
                "Join the voice channel the bot is playing in to clear it."
            )
            return
        await self.clear_queue(self, self.bot, ctx.guild)
        await ctx.send(
            f"cleared by {ctx.author.mention} on {discord.utils.format_dt(datetime.now())} ."
        )

    @staticmethod
    async def disconnect_player(self, bot: commands.Bot, guild: discord.Guild):
        """_summary_
        Args:
            bot (commands.Bot): _description_
            guild (discord.Guild): _description_
        """
        player = self.wavelink_node.get_player(guild)

        # need to check this because this will be fired two times
        # if disconnected using commands
        if player is not None:
            await player.stop()
            player.queue.clear()
            await player.disconnect()


    @staticmethod
    async def clear_queue(self, bot: commands.Bot, guild: discord.Guild):
        player = self.wavelink_node.get_player(guild)
        if player is not None:
            await player.stop()
            player.queue.clear()  

    async def add_spotify_track(self, ctx: commands.Context, track: wavelink.PartialTrack):
        """_summary_
        Args:
            ctx (commands.Context): _description_
            track (wavelink.PartialTrack): _description_
        """
        if not track:
            await ctx.send("No tracks found.")
            return

        vc: wavelink.Player = ctx.voice_client
        await vc.queue.put_wait(track)

        #await ctx.send(f"Added {track.title} to the queue.", delete_after=20)

        if not vc.is_playing() and not vc.queue.is_empty:
            await ctx.send(f"Now playing: {track.title}")
            await vc.play(await vc.queue.get_wait())
        elif not vc.is_playing() and vc.queue.is_empty:
            await ctx.send(f"Now playing: {track.title}")
            await vc.play(track)


    

async def setup(bot):
    await bot.add_cog(Music(bot))