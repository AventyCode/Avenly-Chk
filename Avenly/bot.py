import sys
import os
import re
import logging
import json
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

from commands import start, gen, bin

VALID_PREFIXES = ['.', '-', '$', '!', '¡', '/']

async def flexible_command_handler(update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador flexible para comandos con diferentes prefijos"""
    try:
        text = update.message.text.strip()
        logger.info(f"Mensaje recibido: {text}")
        
        for prefix in VALID_PREFIXES:
            if text.startswith(prefix):
                command_text = text[len(prefix):].strip()
                
                parts = command_text.split(maxsplit=1)
                command = parts[0].lower() if parts else ""
                args_text = parts[1] if len(parts) > 1 else ""
                
                logger.info(f"Prefijo detectado: '{prefix}', Comando: '{command}', Args: '{args_text}'")
                
                if command == "gen":
                    await gen.gen_command(update, context, args_text)
                elif command == "start":
                    await start.start(update, context)
                elif command == "bin":
                    await bin.bin_command(update, context, args_text)
                else:
                    await update.message.reply_text(f"Comando no reconocido: {command}")
                return
        
        logger.info("El mensaje no comienza con un prefijo válido")
    except Exception as e:
        logger.error(f"Error en flexible_command_handler: {e}", exc_info=True)
        await update.message.reply_text("❌ Ocurrió un error al procesar tu comando")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador de errores global"""
    logger.error(f"Update: {update} caused error: {context.error}", exc_info=True)
    if update.message:
        await update.message.reply_text(f"❌ Ocurrió un error: {context.error}")

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, flexible_command_handler))
    
    application.add_handler(CommandHandler("gen", gen.gen_command_wrapper))
    application.add_handler(CommandHandler("start", start.start))
    application.add_handler(CommandHandler("bin", bin.bin_command_wrapper))
    
    application.add_handler(CallbackQueryHandler(gen.regen_callback))

    application.add_error_handler(error_handler)
    
    logger.info("Bot iniciado. Presiona Ctrl+C para detenerlo.")
    application.run_polling()

if __name__ == "__main__":
    main()