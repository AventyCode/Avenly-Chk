import re
import random
import time
import requests
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

logger = logging.getLogger(__name__)

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import luhn_checksum, extract_card_data

BIN_API_URL = "https://bins.antipublic.cc/bins/"

def escape_markdown(text: str) -> str:
    """Escapa caracteres especiales para MarkdownV2"""
    if text is None:
        return "UNKNOWN"
    escape_chars = r'_*[]()~`>#+\-={}.!|'
    return ''.join(['\\' + char if char in escape_chars else char for char in text])

def get_card_length(bin_prefix: str) -> int:
    """Determina la longitud de la tarjeta basado en el BIN"""
    if bin_prefix.startswith('3'):
        return 15  # American Express
    elif bin_prefix.startswith('62'):
        return 19  # UnionPay
    else:
        return 16  # Visa/Mastercard/otros

def generate_card_number(base_card: str, total_length: int) -> str:
    """Genera un número de tarjeta completo con longitud específica"""
    cleaned = ''.join([c for c in base_card if c in '0123456789xX'])
    base_digits = ''.join([
        c if c not in 'xX' else str(random.randint(0, 9))
        for c in cleaned
    ])
    
    if len(base_digits) > total_length - 1:
        base_digits = base_digits[:total_length - 1]
    
    remaining = total_length - 1 - len(base_digits)
    if remaining > 0:
        random_part = ''.join(str(random.randint(0, 9)) for _ in range(remaining))
    else:
        random_part = ''
    
    temp_card = base_digits + random_part
    check_digit = luhn_checksum(temp_card)
    return temp_card + str(check_digit)

def generate_related_card_numbers(base_card: str, count: int = 10) -> list:
    """Genera números de tarjeta relacionados basados en el número base"""
    card_numbers = []
    
    bin_digits = ''.join([c for c in base_card[:6] if c.isdigit()])
    if len(bin_digits) < 6:
        bin_digits = bin_digits.ljust(6, '0')[:6]
    
    total_length = get_card_length(bin_digits)
    
    for _ in range(count):
        card_number = generate_card_number(base_card, total_length)
        card_numbers.append(card_number)
    
    return card_numbers

async def generate_card_response(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                base_card: str, base_date: str, base_cvv: str,
                                bin_digits: str, bin_data: dict, 
                                user_month: str, user_year: str,
                                is_regen: bool = False) -> str:
    """Función compartida para generar la respuesta de tarjetas (para comando y RE-GEN)"""
    start_time = time.time()
    separator = r' \-' * 25
    
    card_numbers = generate_related_card_numbers(base_card, count=10)
    
    cards = []
    for card_number in card_numbers:
        if user_month and user_year:
            month = user_month
            year = user_year
        else:
            month = str(random.randint(1, 12)).zfill(2)
            year = str(random.randint(2025, 2035))
        
        current_is_amex = card_number.startswith('3') and len(card_number) == 15
        
        if base_cvv != "XXX":
            cvv = base_cvv
            if current_is_amex and len(cvv) != 4:
                cvv = str(random.randint(1000, 9999))
            elif not current_is_amex and len(cvv) != 3:
                cvv = str(random.randint(100, 999))
        else:
            if current_is_amex:
                cvv = str(random.randint(1000, 9999))
            else:
                cvv = str(random.randint(100, 999))
        
        cards.append(f"`{card_number}|{month}|{year}|{cvv}`")
    
    elapsed_time = time.time() - start_time
    username = update.callback_query.from_user.username if is_regen and update.callback_query else (
        update.message.from_user.username if update.message else "N/A"
    )
    if not username:
        username = "N/A"
    
    base_date_display = base_date.replace('/', '|')
    base_cvv_display = base_cvv if base_cvv != "XXX" else "rnd"
    
    response = (
        "[滅](https://t.me/destryreferencias) 𝗗𝗲𝘀𝘁𝗿𝘆 𝗖𝗵𝗸 \\| Generated Card:\n"
        f"{separator}\n"
        f" \\- `{base_card}|{base_date_display}|{base_cvv_display}`\n"
        f"{separator}\n"
        + "\n".join(cards) + "\n"
        f"{separator}\n"
    )
    
    if bin_data:
        brand = escape_markdown(bin_data.get('brand'))
        type_ = escape_markdown(bin_data.get('type'))
        level = escape_markdown(bin_data.get('level'))
        bank = escape_markdown(bin_data.get('bank'))
        country_name = escape_markdown(bin_data.get('country_name'))
        country_flag = bin_data.get('country_flag', '')
        
        response += (
            f"*Info*: `{brand} \\- {type_} \\- {level}`\n"
            f"*Bank*: `{bank}`\n"
            f"*Country*: `{country_name} {country_flag}`\n"
        )
    else:
        response += (
            f"*Info*: \n"
            f"*Bank*: \n"
            f"*Country*: \n"
        )
    
    response += (
        f"{separator}\n"
        f"*Gen By*: @{escape_markdown(username)}\n"
        f"*Time*: {escape_markdown(f'{elapsed_time:.2f}')}s\n"
    )
    
    return response

async def gen_command(update: Update, context: ContextTypes.DEFAULT_TYPE, args_text: str) -> None:
    """Maneja el comando /gen con diferentes prefijos"""
    try:
        logger.info(f"Ejecutando gen_command con args: '{args_text}'")
        
        if not args_text:
            separator = r' \-' * 25
            help_message = (
                "[滅](https://t.me/destryreferencias) __𝗗𝗲𝘀𝘁𝗿𝘆 𝗖𝗵𝗸__ \\| *__Generate Card__*:\n"
                f"{separator}\n"
                "*Invalid Command\\!* ⚠️\n"
                f"{separator}\n"
                "*Command*: \\/gen `CC\\|MM\\|YY\\|CVV`\n"
            )
            
            await update.message.reply_text(
                help_message,
                parse_mode="MarkdownV2"
            )
            return

        card_data = extract_card_data(args_text)
        base_card = card_data['cardNumber']
        base_date = card_data['monthYear']
        base_cvv = card_data['cvv']
        
        logger.info(f"Datos extraídos: {card_data}")
        
        bin_digits = ''.join([c for c in base_card[:6] if c.isdigit()])
        bin_to_query = bin_digits if bin_digits and len(bin_digits) >= 6 else "000000"
        
        logger.info(f"Consultando API para BIN: {bin_to_query}")
        
        bin_data = None
        try:
            response = requests.get(f"{BIN_API_URL}{bin_to_query}", timeout=5)
            if response.status_code == 200:
                bin_data = response.json()
                logger.info(f"Datos del BIN obtenidos: {bin_data}")
            else:
                logger.warning(f"API respondió con código: {response.status_code}")
        except Exception as e:
            logger.error(f"Error al consultar API: {e}", exc_info=True)
        
        user_month = None
        user_year = None
        if base_date != "XX/XX":
            try:
                user_month, year_part = base_date.split('/')
                if len(year_part) == 2:
                    user_year = f"20{year_part}" 
                else:
                    user_year = year_part
            except Exception as e:
                logger.error(f"Error al procesar fecha: {e}")

        response = await generate_card_response(
            update, context,
            base_card, base_date, base_cvv,
            bin_digits, bin_data,
            user_month, user_year
        )
        
        callback_id = f"regen_{int(time.time())}_{random.randint(1000, 9999)}"
        context.chat_data[callback_id] = {
            "c": base_card,
            "d": base_date,
            "v": base_cvv,
            "m": user_month,
            "y": user_year,
            "b": bin_to_query
        }
        
        keyboard = [
            [InlineKeyboardButton("RE-GEN", callback_data=callback_id)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            response,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup,
            reply_to_message_id=update.message.message_id
        )
        logger.info("Respuesta enviada correctamente")
    
    except ValueError as e:
        error_msg = f"❌ Error: {str(e)}\nFormato válido: [prefijo]gen <número>[/<mm>/<aa>/<cvv>]"
        await update.message.reply_text(error_msg)
        logger.warning(error_msg)
    except Exception as e:
        error_msg = f"❌ Error inesperado: {str(e)}"
        await update.message.reply_text(error_msg)
        logger.error(error_msg, exc_info=True)

async def regen_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el callback de RE-GEN"""
    query = update.callback_query
    await query.answer()
    
    try:
        callback_id = query.data
        data = context.chat_data.get(callback_id)
        
        if not data:
            await query.edit_message_text("❌ Error: Datos de regeneración no encontrados")
            return
        
        base_card = data["c"]
        base_date = data["d"]
        base_cvv = data["v"]
        user_month = data["m"]
        user_year = data["y"]
        bin_to_query = data["b"]
        
        bin_digits = ''.join([c for c in base_card[:6] if c.isdigit()])
        if len(bin_digits) < 6:
            bin_digits = bin_digits.ljust(6, '0')[:6]
        
        bin_data = None
        if bin_to_query and bin_to_query != "000000":
            try:
                response = requests.get(f"{BIN_API_URL}{bin_to_query}", timeout=5)
                if response.status_code == 200:
                    bin_data = response.json()
                    logger.info(f"Datos del BIN obtenidos en RE-GEN: {bin_data}")
            except Exception as e:
                logger.error(f"Error al consultar API en RE-GEN: {e}", exc_info=True)
        
        response = await generate_card_response(
            update, context,
            base_card, base_date, base_cvv,
            bin_digits, bin_data,
            user_month, user_year,
            is_regen=True
        )
        
        keyboard = [
            [InlineKeyboardButton("RE-GEN", callback_data=callback_id)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=response,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup
        )
        logger.info("RE-GEN realizado correctamente")
    
    except Exception as e:
        error_msg = f"❌ Error en RE-GEN: {str(e)}"
        await query.edit_message_text(error_msg)
        logger.error(error_msg, exc_info=True)

async def gen_command_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Wrapper para el comando /gen estándar"""
    args_text = " ".join(context.args) if context.args else ""
    await gen_command(update, context, args_text)