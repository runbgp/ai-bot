import os
import discord
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import asyncio

description = '''A Discord bot that uses an OpenAI API-compatible API to interact with LLMs from Discord.'''

load_dotenv()

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

        if self.user in message.mentions:
            guild_prompt = self.custom_prompts.get(message.guild.id, prompt)

            async with message.channel.typing():
                user_message_content = f"{message.author.name}: {message.content}"
                
                loop = asyncio.get_event_loop()
                chat_response = await loop.run_in_executor(None, lambda: openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": guild_prompt},
                        {"role": "user", "content": user_message_content},
                    ]
                ))

                response_content = chat_response.choices[0].message.content
                mention = f'{message.author.mention} '
                for i in range(0, len(response_content), 2000 - len(mention)):
                    await message.channel.send(f'{mention}{response_content[i:i+2000-len(mention)]}')

discord_client = AIBot(intents=intents)
discord_client.run(discord_bot_token)
