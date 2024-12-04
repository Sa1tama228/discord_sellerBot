import disnake
from disnake.ext import commands
from plugins import load
from rate_limiter import RateLimiter
from commands import setup_commands

# config.json
config = load()

# config.json
intents = disnake.Intents.all()
bot = commands.Bot(command_prefix=config['prefix'], intents=intents)

# Подключение middleware для ограничения запросов
bot.add_cog(RateLimiter(bot))

# инит когов и функций из commands.py
setup_commands(bot)

@bot.event
async def on_ready():
    print(f'Бот {bot.user.name} успешно запущен и готов к работе!')

if __name__ == "__main__":
    bot.run(config['token'])
