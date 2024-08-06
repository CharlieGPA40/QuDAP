import requests

# Step 1: Function to get chat ID# Step 2: Function to send notification
def send_telegram_notification(message, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    response = requests.post(url, data=data)
    return response.json()

# Replace with your actual bot token
bot_token = "7345322165:AAErDD6Qb8b0xjb0lvQKsHyRGJQBDTXKGwE"
url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
print(requests.get(url).json())
# Get chat ID
chat_id = get_chat_id(bot_token)

# If chat ID is found, send a notification
if chat_id:
    send_telegram_notification("The measurement has been completed successfully.", bot_token, chat_id)
