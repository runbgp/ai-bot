import os
import discord
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import asyncio

description = '''A Discord bot that uses an OpenAI API-compatible API to interact with LLMs from Discord.'''

load_dotenv()

required_env_vars = {
    "discord_bot_token": os.getenv("discord_bot_token"),
    "openai_api_base": os.getenv("openai_api_base"),
    "openai_api_key": os.getenv("openai_api_key"),
    "model": os.getenv("model"),
    "prompt": os.getenv("prompt"),
}

missing_vars = [var for var, value in required_env_vars.items() if not value]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

discord_bot_token = os.getenv("discord_bot_token")
openai_api_base = os.getenv("openai_api_base")
openai_api_key = os.getenv("openai_api_key")
model = os.getenv("model")
prompt = os.getenv("prompt")

openai_client = OpenAI(
    base_url=openai_api_base,
    api_key=openai_api_key
)

intents = discord.Intents.default()
intents.message_content = True

class AIBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_prompts = {}
        self.message_history = {}
        self.history_limit = 10

    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith('#prompt'):
            _, *args = message.content.split()
            if args:
                if args[0] == 'reset':
                    self.custom_prompts[message.guild.id] = prompt
                    await message.channel.send('Prompt has been reset to default.')
                else:
                    self.custom_prompts[message.guild.id] = ' '.join(args)
                    await message.channel.send(f'Custom prompt has been set: ```{self.custom_prompts[message.guild.id]}```')
            else:
                current_prompt = self.custom_prompts.get(message.guild.id, prompt)
                await message.channel.send('Usage: `#prompt [reset|your custom prompt]`')
                await message.channel.send(f'Current prompt: ```{current_prompt}```')
            return

        if message.content.startswith('#clear'):
            if message.channel.id in self.message_history:
                self.message_history[message.channel.id] = []
                await message.channel.send('Conversation history has been cleared.')
            return

        if self.user in message.mentions:
            try:
                guild_prompt = self.custom_prompts.get(message.guild.id, prompt)
                
                if message.channel.id not in self.message_history:
                    self.message_history[message.channel.id] = []
                
                async with message.channel.typing():
                    user_message_content = f"{message.author.name}: {message.content}"
                    
                    # Add user's message to history
                    self.message_history[message.channel.id].append({
                        "role": "user",
                        "content": user_message_content
                    })
                    
                    # Construct messages array with history
                    messages = [{"role": "system", "content": guild_prompt}]
                    messages.extend(self.message_history[message.channel.id][-self.history_limit:])
                    
                    loop = asyncio.get_event_loop()
                    chat_response = await loop.run_in_executor(None, lambda: openai_client.chat.completions.create(
                        model=model,
                        messages=messages
                    ))

                    response_content = chat_response.choices[0].message.content
                    
                    # Add assistant's response to history
                    self.message_history[message.channel.id].append({
                        "role": "assistant",
                        "content": response_content
                    })
                    
                    # Trim history if it exceeds the limit
                    if len(self.message_history[message.channel.id]) > self.history_limit * 2:  # *2 because we store pairs of messages
                        self.message_history[message.channel.id] = self.message_history[message.channel.id][-self.history_limit * 2:]
                    
                    mention = f'{message.author.mention} '
                    for i in range(0, len(response_content), 2000 - len(mention)):
                        await message.channel.send(f'{mention}{response_content[i:i+2000-len(mention)]}')
            except Exception as e:
                await message.channel.send(f"{message.author.mention} Sorry, I encountered an error: {str(e)}")

discord_client = AIBot(intents=intents)
discord_client.run(discord_bot_token)
