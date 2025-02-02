import os, discord, wavelink, json
from discord.ext import commands
##########################################################

with open('config.json') as f:
    config = json.load(f)
token = config.get("token")
prefix = config.get("prefix")
owner = config.get("owner_id")

bot = commands.Bot(command_prefix=prefix, self_bot=True)
bot.remove_command('help')

@bot.event
async def on_ready():
    os.system('cls' if os.name == 'nt' else 'clear')  
    print(f"Shadow Music Selfbot\n")
    print(f"Join Discord Server For More Codes")
    print(f"https://discord.gg/n8MUXvsz4V | discord.gg/automate\n")  
    print(f"[+] Connected: {bot.user.name}")
    try:
        with open('lavalink.json', 'r') as f:
            config = json.load(f)
        sex = config['host']
        port = config['port']
        no = config['password']
        real = config['https']
        uri = f"https://{sex}:{port}" if real else f"http://{sex}:{port}"
        nodes = [wavelink.Node(uri=uri, password=no)]
        await wavelink.Pool.connect(nodes=nodes, client=bot, cache_capacity=100)
        print("[+] Connected to Wavelink")
    except Exception as e:
        print(f"[-] Failed to connect to Wavelink: {e}")


queues = {}
looping = {}

@bot.event
async def on_message(message):
    if not message.guild:
        return        
    if message.author.id == owner:
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
                for track in tracks.tracks:
                    if message.guild.id not in queues:
                        queues[message.guild.id] = []
                    queues[message.guild.id].append(track)
                await message.channel.send(f"Added the playlist {tracks.name} with {len(tracks.tracks)} songs to the queue.")
            else:
                track = tracks[0]
                if message.guild.id not in queues:
                    queues[message.guild.id] = []
                queues[message.guild.id].append(track)
                await message.channel.send(f"Added {track.title} to the queue.")
            if not player.current and queues[message.guild.id]:
                next_track = queues[message.guild.id].pop(0)
                await player.play(next_track, volume=30)
                await message.channel.send(f"Now playing: {next_track.title}")
 
        elif message.content.startswith(f"{prefix}loop"):
            guild_id = message.guild.id
            player = message.guild.voice_client
            if not player or not player.current:
                await message.channel.send("No track is currently playing.")
                return
            if guild_id not in looping:
                looping[guild_id] = 'none' 
            if looping[guild_id] == 'none':
                looping[guild_id] = 'track'
                await message.channel.send(f"Looping the current track: {player.current.title}")
            elif looping[guild_id] == 'track':
                looping[guild_id] = 'queue'
                await message.channel.send(f"Looping the queue.")
            elif looping[guild_id] == 'queue':
                looping[guild_id] = 'none'
                await message.channel.send("Looping disabled.")
                await player.stop()
            else:
                looping[guild_id] = 'none'
                await message.channel.send("Looping disabled.")
                await player.stop()

        elif message.content.startswith(f"{prefix}skip"):
            player = message.guild.voice_client
            if player:
                if message.guild.id in queues and queues[message.guild.id]:
                    next_track = queues[message.guild.id].pop(0)
                    await player.play(next_track, volume=30)
                    await message.channel.send(f"Now playing: {next_track.title}")
                else:
                    await player.stop()
                    await message.channel.send("No more songs in the queue. Leaving the voice channel.")
                    await player.disconnect()

        elif message.content.startswith(f"{prefix}queue"):
            guild_id = message.guild.id
            if guild_id not in queues or not queues[guild_id]:
                await message.channel.send("The queue is currently empty.")
            else:
                queue_list = queues[guild_id]
                queue_text = "\n".join([f"{i+1}. {track.title}" for i, track in enumerate(queue_list)])
                await message.channel.send(f"Current Queue:\n```{queue_text}```")

        elif message.content.startswith(f"{prefix}stop"):
            player = message.guild.voice_client
            if player:
                await player.stop(force=True)
                await message.reply("✅ | Successfully Stopped")

        elif message.content.startswith(f"{prefix}volume"):
            try:
                value = int(message.content[len(f"{prefix}volume "):].strip())
            except ValueError:
                await message.channel.send("Please provide a valid volume level.")
                return
            player = message.guild.voice_client
            if player:
                await player.set_volume(value)
                await message.reply(f"Set the volume to {value}")

        elif message.content.startswith(f"{prefix}dc"):
            player = message.guild.voice_client
            guild_id = message.guild.id
            if player:
                if guild_id in queues:
                    queues[guild_id].clear()
                await player.disconnect()
                await message.reply("✅ | Successfully disconnected.")
            else:
                await message.reply("❌ | I'm not connected to any voice channel.")

        elif message.content.startswith(f"{prefix}help"):
                    await message.reply(f"""
        > # Shadow Music Cmds
        > 
        > {prefix}play [song-name]
        > {prefix}queue
        > {prefix}dc
        > {prefix}stop
        > {prefix}skip
        > {prefix}volume [int]
        > {prefix}loop
        """)
    else:
        return            
    await bot.process_commands(message)

@bot.event
async def on_wavelink_track_end(player, track, reason):
    guild_id = player.guild.id
    if guild_id not in looping:
        return

    if looping[guild_id] == 'track':
        await player.play(track)

    elif looping[guild_id] == 'queue' and queues.get(guild_id):
        queues[guild_id].append(track)
        next_track = queues[guild_id].pop(0)
        await player.play(next_track)

bot.run(token)
