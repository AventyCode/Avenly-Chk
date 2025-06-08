from telegram import Update
from telegram.ext import ContextTypes
from utils import escape_markdown

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    username = user.username if user.username else "N/A"
    user_id = user.id
    
    start_message = (
        "[滅](https://t.me/destryreferencias) 𝗗𝗲𝘀𝘁𝗿𝘆 𝗖𝗵𝗸 \\| *__𝖧𝗈𝗆𝖾__*\n"
        f"\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\n"
        f"[｢滅｣](https://t.me/destryreferencias) *User*: @{escape_markdown(username)}\n"
        f"[｢滅｣](https://t.me/destryreferencias) *Id*: {user_id}\n"
        f"[｢滅｣](https://t.me/destryreferencias) *Suscription*: \n"
        f"\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\n"
        "*To see my available commands just use* /cmds*, and if you have any questions contact me* @L3nSuS\\."
    )
    
    await update.message.reply_text(
        start_message,
        parse_mode="MarkdownV2"
    )