import os, discord, wavelink, json
from discord.ext import commands
##########################################################

with open('config.json') as f:
    config = json.load(f)
token = config.get("token")
prefix = config.get("prefix")
bot = commands.Bot(command_prefix=prefix, self_bot=True)
bot.remove_command('help')

@bot.event
async def on_ready():
    os.system('cls' if os.name == 'nt' else 'clear')    
    print(f"Connected: {bot.user.name}")
    try:
        host = "lava-v4.ajieblogs.eu.org"
        port = 443
        password = "https://dsc.gg/ajidevserver"
        https = True 
        uri = f"https://{host}:{port}" if https else f"http://{host}:{port}"
        nodes = [wavelink.Node(uri=uri, password=password)]
        await wavelink.Pool.connect(nodes=nodes, client=bot, cache_capacity=100)
        print("Connected to Wavelink")
    except Exception as e:
        print(f"Failed to connect to Wavelink: {e}")


@bot.event
async def on_message(message):
    reaction_emoji = '<:Lr_black_crown:1314326554918260883>'
    if not message.guild:
        return
    #if message.author.id == 955721842675560462 or message.content.startswith(f"<@955721842675560462>"):
    #    await message.add_reaction(reaction_emoji)          
    if message.author.id == 955721842675560462:    
        if message.content.startswith(f"{prefix}play"):
            query = message.content[len(f"{prefix}play "):]
            player = message.guild.voice_client

            if not player:
                try:
                    if not message.author.voice:
                        await message.channel.send("Please join a voice channel first before using this command.")
                        return
                    player = await message.author.voice.channel.connect(cls=wavelink.Player)
                except discord.ClientException:
                    await message.channel.send("I was unable to join your voice channel. Please try again.")
                    return

            tracks = await wavelink.Playable.search(query)
            if not tracks:
                await message.channel.send(f"{message.author.mention} - Could not find any tracks with that query. Please try again.")
                return

            if isinstance(tracks, wavelink.Playlist):
                added = await player.queue.put_wait(tracks)
                await message.channel.send(f"Added the playlist {tracks.name} with {added} songs to the queue.")
            else:
                track = tracks[0]
                await player.queue.put_wait(track)
                await message.channel.send(f"Playing {track.title}")
            
            if not player.playing:
                await player.play(player.queue.get(), volume=30)
                
        elif message.content.startswith(f"{prefix}skip"):
            player = message.guild.voice_client
            if player:
                await player.skip(force=True)
                await message.add_reaction("\u2705")

        elif message.content.startswith(f"{prefix}stop"):
            player = message.guild.voice_client
            if player:
                await player.stop(force=True)
                await message.add_reaction("\u2705")

        elif message.content.startswith(f"{prefix}volume"):
            try:
                value = int(message.content[len(f"{prefix}volume "):].strip())
            except ValueError:
                await message.channel.send("Please provide a valid volume level.")
                return

            player = message.guild.voice_client
            if player:
                await player.set_volume(value)
                await message.add_reaction("\u2705")

        elif message.content.startswith(f"{prefix}dc"):
            player = message.guild.voice_client
            if player:
                await player.disconnect()
                await message.add_reaction("\u2705")
        elif message.content.startswith(f"{prefix}help"):
                    await message.channel.send(f"""
        > # Shadow Music Selfbot Cmds
        > 
        > {prefix}play [song-name]
        > {prefix}dc
        > {prefix}stop
        > {prefix}skip
        > {prefix}volume [int]
        """)
    else:
        return            
    await bot.process_commands(message)

bot.run(token)