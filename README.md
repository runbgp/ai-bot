# AI Bot

AI Bot is a Discord bot that uses an OpenAI API-compatible API to interact with LLMs from Discord.

## Running the bot

1. Clone the repository. 
2. Install the required Python packages. `pip install -r requirements.txt`
3. Rename the `.env.example` file to `.env` and populate the following environment variables:
    - `discord_bot_token`: Your Discord bot token.
    - `openai_api_base`: Your OpenAI API base.
    - `openai_api_key`: Your OpenAI API key.
    - `model`: Your model.
    - `prompt`: Your prompt.
4. Run the bot. `python3 ai-bot.py`

## Running with Docker

### Docker Compose

1. Create a `docker-compose.yml` file using the example below.
```yaml
version: '3.8'

services:
  ai-bot:
    image: ghcr.io/runbgp/ai-bot:latest
    restart: unless-stopped
    container_name: ai-bot
    volumes:
      - .env:/.env
```
2. Rename the `.env.example` file to `.env` and populate the following environment variables:
    - `discord_bot_token`: Your Discord bot token.
    - `openai_api_base`: Your OpenAI API base.
    - `openai_api_key`: Your OpenAI API key.
    - `model`: Your model.
    - `prompt`: Your prompt.
3. Pull the latest container. `docker pull ghcr.io/runbgp/ai-bot:latest`
4. Run the bot. `docker compose up -d`

## Contributing

Contributions are always welcome. Please feel free to submit an issue or a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
