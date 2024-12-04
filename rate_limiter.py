from disnake.ext import commands
import time

class RateLimiter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_requests = {}
        self.blocked_users = {}

    @commands.Cog.listener()
    async def on_command(self, ctx):
        user_id = ctx.author.id
        current_time = time.time()

        # Если пользователь заблокирован, проверяем, истекло ли время блокировки
        if user_id in self.blocked_users:
            if current_time < self.blocked_users[user_id]["until"]:
                # Пользователь заблокирован, и мы уже отправили сообщение
                return
            else:
                # Снимаем блокировку, если время истекло
                del self.blocked_users[user_id]

        # Инициализация трекинга запросов пользователя
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []

        # Добавляем текущее время запроса
        self.user_requests[user_id].append(current_time)

        # Удаляем запросы, которые старше 10 секунд
        self.user_requests[user_id] = [t for t in self.user_requests[user_id] if current_time - t <= 10]

        # Проверяем, превысил ли пользователь лимит
        if len(self.user_requests[user_id]) > 5:
            # Блокируем пользователя на 20 секунд и отправляем одно сообщение
            self.blocked_users[user_id] = {"until": current_time + 20, "notified": False}
            if not self.blocked_users[user_id]["notified"]:
                await ctx.send("Вы заблокированы за слишком частые запросы. Попробуйте через 20 секунд.")
                self.blocked_users[user_id]["notified"] = True
            del self.user_requests[user_id]  # Сбрасываем счетчик запросов
            return

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Подождите {round(error.retry_after, 2)} секунд перед следующим использованием команды.")
