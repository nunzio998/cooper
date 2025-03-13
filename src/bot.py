import logging
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from utils.utils import read_json, get_user_collection, chat_with_deepseek, get_user_context

# Carica la configurazione
conf = read_json("utils/config.json")
BOT_TOKEN = conf["BOT_TOKEN"]

# Configura logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)


# Funzione per gestire i messaggi
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    user_text = update.message.text

    # Ottieni la collection dell'utente (creata automaticamente se non esiste)
    user_collection = get_user_collection(user_id)

    # Recupera il contesto della conversazione
    context_data = get_user_context(user_collection)

    # Chiamata a DeepSeek per generare la risposta
    bot_reply = chat_with_deepseek(user_text, context_data)

    # Salva il messaggio dell'utente con timestamp
    user_collection.insert_one({
        "role": "user",
        "content": user_text,
        "timestamp": datetime.datetime.now()
    })

    # Salva la risposta del bot con timestamp
    user_collection.insert_one({
        "role": "assistant",
        "content": bot_reply,
        "timestamp": datetime.datetime.now()
    })

    await update.message.reply_text(bot_reply)


# Comando start
async def start(update: Update, context: CallbackContext) -> None:
    user_name = update.message.from_user.first_name
    await update.message.reply_text(f"Ciao {user_name}, sono Cooper! 😊")


# Configurazione del bot
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Bot in esecuzione con DeepSeek...")
    app.run_polling()


if __name__ == "__main__":
    main()
