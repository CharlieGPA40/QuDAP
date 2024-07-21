import requests

# bot_token = "7345322165:AAErDD6Qb8b0lvQKsHyRGJQBDTXKGwE"
# chat_id = "5733353343"
# image_path = "R:\GitHub\Data_Processing_Suite\GUI\QDesign\Reference\Keithley6221DC.png"  # Replace with your image path
# url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
# data = {"chat_id": chat_id}
#
# with open(image_path, "rb") as image_file:
#     files = {"photo": image_file}
#     response = requests.post(url, data=data, files=files)
#     print(response.json())

def send_telegram_notification(message):
    bot_token = "7345322165:AAErDD6Qb8b0xjb0lvQKsHyRGJQBDTXKGwE"
    chat_id = "5733353343"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    response = requests.post(url, data=data)
    return response.json()

send_telegram_notification("Test")

import requests


def send_image(bot_token, chat_id, image_path, caption=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    data = {"chat_id": chat_id}
    if caption:
        data["caption"] = caption

    try:
        with open(image_path, "rb") as image_file:
            files = {"photo": image_file}
            response = requests.post(url, data=data, files=files)

        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code}, {response.text}")

        return response.json()

    except FileNotFoundError:
        return {"ok": False, "error": "File not found. Check the file path."}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# Replace with your new bot token
bot_token = "7345322165:AAErDD6Qb8b0xjb0lvQKsHyRGJQBDTXKGwE"
chat_id = "5733353343"
image_path = "GUI\QDesign\Reference\Keithley6221DC.png"  # Replace with your image path
caption = "Here is an image for you!"  # Optional caption

response = send_image(bot_token, chat_id, image_path, caption)
print(response)
