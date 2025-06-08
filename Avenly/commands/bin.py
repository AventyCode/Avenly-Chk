import re
import time
import requests
import logging
from telegram import Update
from telegram.ext import ContextTypes
from utils import escape_markdown

logger = logging.getLogger(__name__)

BIN_API_URL = "https://bins.antipublic.cc/bins/"

VALID_PREFIXES = ['.', '-', '$', '!', '¡', '/']

async def bin_command(update: Update, context: ContextTypes.DEFAULT_TYPE, args_text: str) -> None:
    """Maneja el comando /bin para verificar información de BINs"""
    full_text = update.message.text.strip()
    bin_str = ""
    
    for prefix in VALID_PREFIXES:
        if full_text.startswith(prefix):
            command_part = full_text[len(prefix):].strip()
            
            if command_part.lower().startswith("bin"):
                bin_str = command_part[3:].strip()
                if not bin_str:
                    bin_str = command_part[3:]
            break

    if not bin_str and args_text:
        bin_str = args_text

    logger.info(f"Texto bin extraído: '{bin_str}'")

    if not bin_str:
        await update.message.reply_text(
            "[滅](https://t.me/destryreferencias) 𝗗𝗲𝘀𝘁𝗿𝘆 𝗖𝗵𝗸 \\| Generate Card\:\n"
            "\\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\-\n"
            "*Invalid Command\\!* ⚠️\n"
            "\\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\- \\-\n"
            "*Command:* \\/bin `BIN`\n",
            parse_mode="MarkdownV2"
        )
        return

    digits = re.findall(r'\d', bin_str)
    if not digits:
        await update.message.reply_text(
            "❌ No se encontraron dígitos en el BIN proporcionado",
            parse_mode="MarkdownV2"
        )
        return

    bin_digits = digits[:6]
    if len(bin_digits) < 6:
        bin_digits = bin_digits + ['0'] * (6 - len(bin_digits))

    bin_to_query = ''.join(bin_digits)
    logger.info(f"Consultando API para BIN: {bin_to_query}")

    start_time = time.time()

    try:
        response = requests.get(f"{BIN_API_URL}{bin_to_query}", timeout=5)
        if response.status_code == 200:
            bin_data = response.json()
            logger.info(f"Datos del BIN obtenidos: {bin_data}")
        else:
            logger.warning(f"API respondió con código: {response.status_code}")
            await update.message.reply_text(
                "❌ No se encontró información para este BIN",
                parse_mode="MarkdownV2"
            )
            return
    except Exception as e:
        logger.error(f"Error al consultar API: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Error al consultar la API de BINs",
            parse_mode="MarkdownV2"
        )
        return

    elapsed_time = time.time() - start_time

    brand = bin_data.get('brand', 'Desconocido')
    card_type = bin_data.get('type', 'Desconocido')
    level = bin_data.get('level', 'Desconocido')
    bank = bin_data.get('bank', 'Desconocido')
    country_name = bin_data.get('country_name', 'Desconocido')
    country_code = bin_data.get('country', 'XX')
    country_flag = bin_data.get('country_flag', '🏳️')

    separator = r' \-' * 15
    response = (
        "[滅](https://t.me/destryreferencias) 𝗗𝗲𝘀𝘁𝗿𝘆 𝗖𝗵𝗸 \\| Checker bin\:\n"
        f"{separator}\n"
        f"*Bin*: `{bin_to_query}`\n"
        f"{separator}\n"
        f"[｢滅｣](https://t.me/destryreferencias) *Brand*: `{escape_markdown(brand)}`\n"
        f"[｢滅｣](https://t.me/destryreferencias) *Type*: `{escape_markdown(card_type)}`\n"
        f"[｢滅｣](https://t.me/destryreferencias) *Level*: `{escape_markdown(level)}`\n"
        f"[｢滅｣](https://t.me/destryreferencias) *Bank*: `{escape_markdown(bank)}`\n"
        f"[｢滅｣](https://t.me/destryreferencias) *Country*: `{country_flag} \\| {country_code} \\| {escape_markdown(country_name)}`\n"
        f"{separator}\n"
        f"[｢滅｣](https://t.me/destryreferencias) *Time*:  {escape_markdown(f'{elapsed_time:.2f}')}s\n"  # Escapado el tiempo
        f"{separator}\n"
        "[滅](https://t.me/destryreferencias)  𝗢𝗪𝗡𝗘𝗥: @L3nSuS"
    )

    await update.message.reply_text(
        response,
        parse_mode="MarkdownV2"
    )
    logger.info("Respuesta de bin enviada correctamente")

async def bin_command_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Wrapper para el comando /bin estándar"""
    args_text = " ".join(context.args) if context.args else ""
    await bin_command(update, context, args_text)