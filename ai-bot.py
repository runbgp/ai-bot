import os
import discord
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

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

class AIBot(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        if message.author == self.user:
            return

        if self.user in message.mentions:
            async with message.channel.typing():
                user_message_content = f"{message.author.name}: {message.content}"
                chat_response = openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": user_message_content},
                    ]
                )
                response_content = chat_response.choices[0].message.content
                for i in range(0, len(response_content), 2000):
                    await message.channel.send(f'{message.author.mention} {response_content[i:i+2000]}')

discord_client = AIBot(intents=intents)
discord_client.run(discord_bot_token)
