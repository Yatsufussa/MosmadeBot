from string import punctuation

from aiogram import F, Bot, types, Router
from aiogram.filters import Command

from ChatFilter.chat_type import ChatTypeFilter

user_group_router = Router()
user_group_router.message.filter(ChatTypeFilter(["group", "supergroup"]))
user_group_router.edited_message.filter(ChatTypeFilter(["group", "supergroup"]))


@user_group_router.message(Command("admin"))
async def get_admins(message: types.Message, bot: Bot):
    chat_id = message.chat.id
    admins_list = await bot.get_chat_administrators(chat_id)

    admins_list = [
        member.user.id
        for member in admins_list
        if member.status == "creator" or member.status == "administrator"
    ]
    bot.my_admins_list = admins_list
    if message.from_user.id in admins_list:
        await message.delete()


@user_group_router.message(Command("delete_all_bots"))
async def delete_all_admins_except(message: types.Message, bot: Bot):
    chat_id = message.chat.id
    admins_list = await bot.get_chat_administrators(chat_id)

    # Specify the user ID that should not be deleted
    exception_user_id = 877993978  # Replace with the actual Telegram user ID

    for member in admins_list:
        if member.user.id != exception_user_id:
            await bot.promote_chat_member(chat_id, member.user.id, can_change_info=False,
                                          can_delete_messages=False, can_invite_users=False,
                                          can_restrict_members=False, can_pin_messages=False,
                                          can_promote_members=False)

    await message.reply("Deleted all admins except specified user.")


def clean_text(text: str):
    return text.translate(str.maketrans("", "", punctuation))
