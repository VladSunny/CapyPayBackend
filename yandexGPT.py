import requests
import os
from dotenv import load_dotenv
from copy import deepcopy
import json

# Load environment variables from .env file
load_dotenv()

ID = os.getenv("GPT_ID")
KEY = os.getenv("GPT_KEY")

# Базовый промпт для анализа покупок
prompt = {
    "modelUri": f"gpt://{ID}/yandexgpt-lite",
    "completionOptions": {
        "stream": False,
        "temperature": 0.6,
        "maxTokens": "2000"
    },
    "messages": [
        {
            "role": "system",
            "text": """Ты финансовый аналитик, который помогает пользователю анализировать их покупки. 
            На основе данных о покупках (теги, количество, цена, даты) ты должен:
            1. Определить наиболее популярные категории покупок.
            2. Выявить тренды расходов (например, рост или снижение трат в определенных категориях).
            3. Дать рекомендации по оптимизации расходов (например, где можно сэкономить).
            Ответ должен быть структурированным, кратким и понятным. Используй примеры из данных, если они есть."""
        }
    ]
}

url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Api-Key {KEY}"
}

def send_request(message):
    cur_prompt = deepcopy(prompt)
    cur_prompt["messages"].append({"role": "user", "text": message})
    response = requests.post(url, headers=headers, json=cur_prompt)
    if response.status_code == 200:
        result = json.loads(response.text)['result']['alternatives'][0]['message']['text']
        return result
    else:
        raise Exception(f"Ошибка API: {response.status_code}, {response.text}")

# Пример использования
# send_request("Анализируй данные: тег 'еда' - 5 покупок, 1000 руб; тег 'одежда' - 2 покупки, 3000 руб.")