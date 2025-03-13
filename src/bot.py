import logging
import requests
import json
import pymongo
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext


# Funzione per leggere la configurazione dal file JSON
def read_json(path) -> dict:
    with open(path, 'r') as file:
        return json.load(file)


# Carica la configurazione
conf = read_json("utils/config.json")
BOT_TOKEN = conf["BOT_TOKEN"]
DEEPSEEK_API_KEY = conf["DEEPSEEK_API_KEY"]
MONGO_URI = conf["MONGO_URI"]
DB_NAME = conf["DB_NAME"]

# Configura logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Connessione a MongoDB
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]


# Funzione per ottenere il nome della collection di un utente
def get_user_collection(user_id):
    collection_name = f"user_{user_id}"

    if collection_name not in db.list_collection_names():
        db.create_collection(collection_name)
        logging.info(f"Creata la collection: {collection_name}")
    else:
        logging.info(f"La collection esiste già: {collection_name}")
    return db.get_collection(collection_name)


# Funzione per interagire con DeepSeek API
def chat_with_deepseek(prompt, context):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": "Sei un assistente personale empatico."}] + context + [
            {"role": "user", "content": prompt}]
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return "Errore nel chatbot DeepSeek."


# Funzione per recuperare il contesto della conversazione di un utente
def get_user_context(user_collection):
    messages = user_collection.find({}, {"_id": 0, "role": 1, "content": 1}).sort("timestamp", pymongo.ASCENDING)
    return list(messages)


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
