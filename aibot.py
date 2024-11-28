import os
import discord
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import asyncio
import random

description = '''A Discord bot that uses an OpenAI API-compatible API to interact with LLMs from Discord.'''

# Load environment variables from .env file
load_dotenv()

# Define and check required environment variables
required_env_vars = {
    "discord_bot_token": os.getenv("discord_bot_token"),
    "openai_api_base": os.getenv("openai_api_base"),
    "openai_api_key": os.getenv("openai_api_key"),
    "model": os.getenv("model"),
    "prompt": os.getenv("prompt"),
}

# Check for any missing environment variables
missing_vars = [var for var, value in required_env_vars.items() if not value]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Extract environment variables
discord_bot_token = os.getenv("discord_bot_token")
openai_api_base = os.getenv("openai_api_base")
openai_api_key = os.getenv("openai_api_key")
model = os.getenv("model")
prompt = os.getenv("prompt")

# Initialize OpenAI client
openai_client = OpenAI(
    base_url=openai_api_base,
    api_key=openai_api_key
)

# Set up Discord intents
intents = discord.Intents.default()
intents.message_content = True

class AIBot(discord.Client):
    """
    A Discord bot that integrates with an OpenAI API-compatible API to provide AI-powered responses.
    Supports custom prompts and maintains conversation history per channel.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_prompts = {}  # Stores custom prompts per guild
        self.message_history = {}  # Stores conversation history per channel
        self.history_limit = 10    # Maximum number of messages to keep in history
        # Add status update task
        self.status_update_task = None

    async def setup_hook(self) -> None:
        """Called before the bot starts running to set up background tasks"""
        self.status_update_task = self.loop.create_task(self.rotate_status())

    async def rotate_status(self):
        """Background task to rotate the bot's status using AI-generated statuses"""
        await self.wait_until_ready()
        
        # Define possible activity types
        activity_types = [
            {"type": "playing", "prompt": "Generate a short game title or gaming activity (max 128 chars). Don't include quotes, punctuation, or words like 'playing' or 'game' at the start."},
            {"type": "listening", "prompt": "Generate a short song or audio title (max 128 chars). Don't include quotes, punctuation, or words like 'listening to' at the start."},
            {"type": "watching", "prompt": "Generate a short movie/show title or watching activity (max 128 chars). Don't include quotes, punctuation, or words like 'watching' at the start."}
        ]
        
        while not self.is_closed():
            try:
                # Randomly select activity type
                activity_type = random.choice(activity_types)
                
                # Generate a new status using the AI
                messages = [{
                    "role": "system",
                    "content": f"You are helping to set Discord status messages. {activity_type['prompt']}. Don't use quotes or explain - just respond with the text. Make them relevant to an AI-based Discord bot, use humor and be creative."
                }, {
                    "role": "user",
                    "content": "Generate a status message"
                }]
                
                status_response = await self.loop.run_in_executor(
                    None,
                    lambda: openai_client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=128,
                        temperature=0.9
                    )
                )
                
                new_status = status_response.choices[0].message.content.strip()
                # Clean up any quotes from the status
                new_status = new_status.replace('"', '').replace("'", "").strip()
                if new_status:
                    # Create appropriate activity based on type
                    if activity_type["type"] == "playing":
                        activity = discord.Game(name=new_status)
                    elif activity_type["type"] == "listening":
                        activity = discord.Activity(type=discord.ActivityType.listening, name=new_status)
                    elif activity_type["type"] == "watching":
                        activity = discord.Activity(type=discord.ActivityType.watching, name=new_status)
                    
                    # Set the new status with a random presence status
                    status_options = [discord.Status.online, discord.Status.idle, discord.Status.do_not_disturb]
                    await self.change_presence(
                        activity=activity,
                        status=random.choice(status_options)
                    )
                    print(f"[{datetime.now()}] Updated status to: {activity_type['type'].title()} {new_status}")
                
                # Wait 5 minutes before next update
                await asyncio.sleep(300)
            except Exception as e:
                print(f"Error updating status: {str(e)}")
                await asyncio.sleep(300)  # Still wait before retrying

    async def on_ready(self):
        """Called when the bot successfully connects to Discord"""
        print('Logged on as', self.user)

    async def on_message(self, message):
        """
        Handles incoming Discord messages.
        Supports commands:
        - #prompt: Set or reset custom prompts
        - #clear: Clear conversation history
        - @mention: Generate AI response
        """
        if message.author == self.user:
            return

        # Handle custom prompt commands
        if message.content.startswith('#prompt'):
            _, *args = message.content.split()
            if args:
                if args[0] == 'reset':
                    self.custom_prompts[message.guild.id] = prompt
                    # Clear history for all channels in this guild
                    for channel_id in list(self.message_history.keys()):
                        if message.guild.get_channel(channel_id):  # Check if channel belongs to this guild
                            self.message_history[channel_id] = []
                    await message.channel.send('Prompt has been reset to default and history has been cleared.')
                else:
                    self.custom_prompts[message.guild.id] = ' '.join(args)
                    # Clear history for all channels in this guild
                    for channel_id in list(self.message_history.keys()):
                        if message.guild.get_channel(channel_id):  # Check if channel belongs to this guild
                            self.message_history[channel_id] = []
                    await message.channel.send(f'Custom prompt has been set and history has been cleared: ```{self.custom_prompts[message.guild.id]}```')
            else:
                current_prompt = self.custom_prompts.get(message.guild.id, prompt)
                await message.channel.send('Usage: `#prompt [reset|your custom prompt]`')
                await message.channel.send(f'Current prompt: ```{current_prompt}```')
            return

        # Handle clear history command
        if message.content.startswith('#clear'):
            if message.channel.id in self.message_history:
                self.message_history[message.channel.id] = []
                await message.channel.send('Conversation history has been cleared.')
            return

        # Handle AI responses when bot is mentioned
        if self.user in message.mentions:
            try:
                guild_prompt = self.custom_prompts.get(message.guild.id, prompt)
                
                # Initialize history for new channels
                if message.channel.id not in self.message_history:
                    self.message_history[message.channel.id] = []
                
                async with message.channel.typing():
                    user_message_content = f"{message.author.name}: {message.content}"
                    
                    # Log user message
                    print(f"[{datetime.now()}] User message in #{message.channel.name}: {user_message_content}")
                    
                    # Add user's message to history
                    self.message_history[message.channel.id].append({
                        "role": "user",
                        "content": user_message_content
                    })
                    
                    # Construct messages array with history
                    messages = [{"role": "system", "content": guild_prompt}]
                    messages.extend(self.message_history[message.channel.id][-self.history_limit:])
                    
                    # Generate AI response
                    loop = asyncio.get_event_loop()
                    chat_response = await loop.run_in_executor(None, lambda: openai_client.chat.completions.create(
                        model=model,
                        messages=messages
                    ))

                    response_content = chat_response.choices[0].message.content
                    
                    # Log bot response
                    print(f"[{datetime.now()}] Bot response in #{message.channel.name}: {response_content}")
                    
                    # Add assistant's response to history
                    self.message_history[message.channel.id].append({
                        "role": "assistant",
                        "content": response_content
                    })
                    
                    # Trim history if it exceeds the limit
                    if len(self.message_history[message.channel.id]) > self.history_limit * 2:  # *2 because we store pairs of messages
                        self.message_history[message.channel.id] = self.message_history[message.channel.id][-self.history_limit * 2:]
                    
                    # Split and send response in chunks to handle Discord's message length limit
                    mention = f'{message.author.mention} '
                    for i in range(0, len(response_content), 2000 - len(mention)):
                        await message.channel.send(f'{mention}{response_content[i:i+2000-len(mention)]}')
            except Exception as e:
                await message.channel.send(f"{message.author.mention} Sorry, I encountered an error: {str(e)}")

# Initialize and run the bot
discord_client = AIBot(intents=intents)
discord_client.run(discord_bot_token)
