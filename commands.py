import disnake
from disnake.ext import commands
from disnake import Interaction, ButtonStyle, MessageInteraction
from disnake.ui import View, Button
from db import get_user, create_user, create_order, get_all_orders, get_user_orders, get_order_by_id, \
    approve_order, reject_order, create_unapproved_order, get_all_unapproved_orders

"""тело бота"""


class OrderDetailView(View):
    def __init__(self, bot: commands.Bot, order):
        super().__init__()
        self.bot = bot
        self.order = order

    @disnake.ui.button(label="Назад в список", custom_id="back_to_orders")
    async def back_to_orders_button(self, button: disnake.ui.Button, interaction: Interaction):
        orders = await get_all_orders()
        await show_orders(interaction, orders)


class OrderSelectView(View):
    def __init__(self, bot: commands.Bot, orders):
        super().__init__()
        self.bot = bot
        for order in orders:
            self.add_item(Button(label=f"Заказ: {order.title}", custom_id=f"order_{order.id}"))


async def show_orders(ctx_or_interaction, orders):
    if orders:
        orders_list = "\n".join([f"📌 **Название:** {order.title}\n💵 **Цена:** {order.client_price} RC." for order in orders])
        if isinstance(ctx_or_interaction, Interaction):
            await ctx_or_interaction.response.send_message(f"**Список всех заказов:**\n\n{orders_list}", view=OrderSelectView(ctx_or_interaction.bot, orders))
        else:
            await ctx_or_interaction.send(f"**Список всех заказов:**\n\n{orders_list}", view=OrderSelectView(ctx_or_interaction.bot, orders))
    else:
        if isinstance(ctx_or_interaction, Interaction):
            await ctx_or_interaction.response.send_message("Нет доступных заказов.")
        else:
            await ctx_or_interaction.send("Нет доступных заказов.")


class AdminOrderApprovalView(View):
    def __init__(self, bot: commands.Bot, order):
        super().__init__()
        self.bot = bot
        if order is None:
            raise ValueError("Order cannot be None")
        self.order = order

    @disnake.ui.button(label="Подтвердить заказ", style=ButtonStyle.green)
    async def approve_button(self, button: disnake.ui.Button, interaction: Interaction):
        await approve_order(self.order.id)
        await interaction.response.send_message("Заказ подтвержден и добавлен в список активных заказов.")
        await self.bot.get_user(self.order.client_id).send("Ваш заказ был подтвержден администратором.")

    @disnake.ui.button(label="Отклонить заказ", style=ButtonStyle.red)
    async def reject_button(self, button: disnake.ui.Button, interaction: Interaction):
        await reject_order(self.order.id)
        await interaction.response.send_message("Заказ отклонен и удален.")
        await self.bot.get_user(self.order.client_id).send("Ваш заказ был отклонен администратором.")


class MainMenuView(View):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @disnake.ui.button(label="Создать заказ", style=ButtonStyle.green, custom_id="create_order")
    async def create_order_button(self, button: disnake.ui.Button, interaction: Interaction):
        user_id = interaction.user.id
        await interaction.response.send_message("Я написал вам в личные сообщения, продолжим там.", ephemeral=True)
        cog = self.bot.get_cog("InteractionHandler")
        if cog:
            await cog.initiate_order_creation(user_id)

    @disnake.ui.button(label="Мои заказы", style=ButtonStyle.blurple, custom_id="my_orders")
    async def my_orders_button(self, button: disnake.ui.Button, interaction: Interaction):
        user_id = interaction.user.id
        orders = await get_user_orders(user_id)
        await show_orders(interaction, orders)

    @disnake.ui.button(label="Список всех заказов", style=ButtonStyle.gray, custom_id="all_orders")
    async def all_orders_button(self, button: disnake.ui.Button, interaction: Interaction):
        orders = await get_all_orders()
        await show_orders(interaction, orders)


class AdminPanelView(View):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @disnake.ui.button(label="Неподтвержденные заказы", style=ButtonStyle.gray)
    async def unapproved_orders_button(self, button: disnake.ui.Button, interaction: Interaction):
        orders = await get_all_unapproved_orders()
        if orders:
            await show_admin_order(interaction, orders[0], orders)
        else:
            await interaction.response.send_message("Нет неподтвержденных заказов.", ephemeral=True)


async def show_admin_order(interaction, order, orders):
    await interaction.response.send_message(f"Заказ:\nЗаголовок: {order.title}\nОписание: {order.description}\nЦена: {order.client_price}",
                                            view=AdminOrderApprovalView(interaction.bot, order))


@commands.command(name="admin_panel")
@commands.has_permissions(administrator=True)
async def admin_panel_command(ctx):
    await ctx.send("Добро пожаловать в админ-панель", view=AdminPanelView(ctx.bot))


class OrderCreationView(View):
    def __init__(self, bot: commands.Bot, user_id: int):
        super().__init__()
        self.bot = bot
        self.user_id = user_id

    @disnake.ui.button(label="Подтвердить", style=ButtonStyle.green)
    async def confirm_button(self, button: disnake.ui.Button, interaction: MessageInteraction):
        cog = self.bot.get_cog("InteractionHandler")
        if cog and self.user_id in cog.user_state:
            state = cog.user_state[self.user_id]
            data = state['data']

            # Создание заказа в unapproved_orders
            new_order = await create_unapproved_order(self.user_id, data['title'], data['description'], data['price'],
                                                      data['item'])

            if new_order is None:
                await interaction.response.send_message("Ошибка при создании заказа.", ephemeral=True)
                return

            await interaction.response.send_message("Ваш заказ был создан и отправлен на рассмотрение.", ephemeral=True)

            # HERE IS ADMIN ID
            admin = await self.bot.fetch_user(12345678910)
            await admin.send(
                f"Новый заказ на подтверждение:\nЗаголовок: {data['title']}\nОписание: {data['description']}\nЦена: {data['price']} RC",
                view=AdminOrderApprovalView(self.bot, new_order))

            del cog.user_state[self.user_id]

    @disnake.ui.button(label="Отмена", style=ButtonStyle.red)
    async def cancel_button(self, button: disnake.ui.Button, interaction: MessageInteraction):
        await interaction.response.send_message("Создание заказа отменено.", ephemeral=True)
        cog = self.bot.get_cog("InteractionHandler")
        if cog and self.user_id in cog.user_state:
            del cog.user_state[self.user_id]


class InteractionHandler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_state = {}

    async def initiate_order_creation(self, user_id: int):
        self.user_state[user_id] = {'step': 1, 'data': {}}
        user = await self.bot.fetch_user(user_id)
        await user.send("Привет! Отошли следующим сообщением заголовок твоего заказа:")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None and message.author.id in self.user_state:
            state = self.user_state[message.author.id]
            step = state['step']

            if step == 1:
                state['data']['title'] = message.content
                state['step'] += 1
                await message.author.send("Окей, теперь дай мне описание:")
            elif step == 2:
                state['data']['description'] = message.content
                state['step'] += 1
                await message.author.send("Теперь укажи цену (только целое число):")
            elif step == 3:
                try:
                    price = int(message.content)
                    state['data']['price'] = price
                    state['step'] += 1
                    await message.author.send("Отлично! Теперь укажи, что выдать покупателю при покупке:")
                except ValueError:
                    await message.author.send("Пожалуйста, укажи цену в виде целого числа.")
            elif step == 4:
                state['data']['item'] = message.content
                state['step'] += 1
                await message.author.send("Проверьте ваш заказ:\n"
                                          f"Заголовок: {state['data']['title']}\n"
                                          f"Описание: {state['data']['description']}\n"
                                          f"Цена: {state['data']['price']} RC\n"
                                          f"Что будет выдано покупателю: {state['data']['item']}\n\n"
                                          "Подтвердите или отмените заказ:",
                                          view=OrderCreationView(self.bot, message.author.id))
            else:
                await message.author.send("Вы уже завершили процесс создания заказа или он был отменен.")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: Interaction):
        custom_id = interaction.data["custom_id"]
        if custom_id == "create_order":
            await interaction.response.send_message("Я написал вам в личные сообщения, продолжим там.", ephemeral=True)
            await self.initiate_order_creation(interaction.user.id)
        elif custom_id.startswith("order_"):
            order_id = int(custom_id.split("_")[1])
            order = await get_order_by_id(order_id)
            if order:
                order_details = (
                    f"**Детали заказа:**\n\n"
                    f"🆔 **ID:** {order.id}\n"
                    f"📌 **Название:** {order.title}\n"
                    f"📝 **Описание:** {order.description}\n"
                    f"💵 **Цена:** {order.client_price} RC.\n"
                )
                await interaction.response.send_message(order_details,
                                                        view=OrderDetailView(self.bot, order),
                                                        ephemeral=True)
            else:
                await interaction.response.send_message("Заказ не найден.", ephemeral=True)

    @commands.command(name="start")
    async def start(self, ctx):
        user = await get_user(ctx.author.id)
        if not user:
            await create_user(ctx.author.id, ctx.author.name)
            await ctx.send("Добро пожаловать! Ваш профиль создан.")
        else:
            await ctx.send(f"С возвращением, {user.username}!")
        await ctx.send("Что бы вы хотели сделать?", view=MainMenuView(self.bot))

    @commands.command(name="create_order")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def create_order_command(self, ctx, title: str, description: str, price: float, item_to_give: str):
        await create_order(ctx.author.id, title, description, price, item_to_give)
        await ctx.send(f"Заказ '{title}' успешно создан!")

    @commands.command(name="my_orders")
    async def my_orders_command(self, ctx):
        orders = await get_user_orders(ctx.author.id)
        await show_orders(ctx, orders)

    @commands.command(name="all_orders")
    async def all_orders_command(self, ctx):
        orders = await get_all_orders()
        await show_orders(ctx, orders)


def setup_commands(bot: commands.Bot):
    bot.add_cog(InteractionHandler(bot))
    print("InteractionHandler cog has been added")
