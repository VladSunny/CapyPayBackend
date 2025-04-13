import requests
import os
from dotenv import load_dotenv
from copy import deepcopy
import json

# Load environment variables from .env file
load_dotenv()

ID = os.getenv("GPT_ID")
KEY = os.getenv("GPT_KEY")

# Улучшенный промпт для анализа покупок
prompt = {
    "modelUri": f"gpt://{ID}/yandexgpt",
    "completionOptions": {
        "stream": False,
        "temperature": 0.5,
        "maxTokens": "2000"
    },
    "messages": [
        {
            "role": "system",
            "text": """Ты финансовый аналитик, который помогает пользователю анализировать их покупки. 
            На основе данных о покупках (теги, количество, цена, даты) ты должен:
            1. Определить наиболее популярные категории покупок (по количеству и сумме трат).
            2. Выявить тренды расходов (рост, снижение или стабильность в категориях за период).
            3. Дать рекомендации по оптимизации расходов (указать, где можно сэкономить, с примерами).

            **Структура ответа**:
            - **Популярные категории**:
              - Список категорий с количеством покупок и общей суммой (например, "Еда: 5 покупок, 1000 руб").
              - Краткий комментарий о доминирующей категории.
            - **Тренды расходов**:
              - Описание изменений расходов по категориям (например, "Траты на одежду выросли на 20% за месяц").
              - Указание периода, если данные позволяют.
            - **Рекомендации**:
              - Конкретные советы по сокращению расходов (например, "Сократить траты на еду, заменив часть покупок более дешевыми аналогами").
              - Примеры из данных для обоснования.

            Ответ должен быть кратким, структурированным (используй заголовки и списки) и основанным на предоставленных данных. Если данных недостаточно, укажи предположения или запроси уточнения."""
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