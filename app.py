from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from supabase import create_client, Client
from io import StringIO
import pandas as pd
from config import caramel_latte_palette
import dotenv
import yandexGPT

dotenv.load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

print(supabase_key)

supabase: Client = create_client(supabase_url, supabase_key)

app = Flask(__name__)

CORS(app, origins=["http://localhost:5173", "https://capy-pay.netlify.app"])

genders = ['M', 'F']
category_top20_list = ['Супермаркеты',
 'Дом и ремонт',
 'Фастфуд',
 'Одежда и обувь',
 'Автоуслуги',
 'Топливо',
 'Рестораны',
 'Финансы',
 'Медицина',
 'Маркетплейсы',
 'Различные товары',
 'Турагентства',
 'Другое',
 'Авиабилеты',
 'Аптеки',
 'Такси',
 'Красота',
 'Сервис',
 'Развлечения',
 'Электроника и техника',
 'Отели']
income_ranges = [[1, 450], [451, 700], [701, 1150], [1151, 1625], [1626, 2100], [2101, 2550], [2551, 3000], [3001, 3450], [3451, 4000], [4000, 18000]]

def assign_income_group(income):
    for i, (low, high) in enumerate(income_ranges):
        if low <= income <= high:
            return f"{low}-{high}"
    return "Unknown"


def get_payments_data():
    response = (
        supabase.table("Payments")
        .select("*")
        .csv()
        .execute()
    )

    df = pd.read_csv(StringIO(response.data), index_col=0, parse_dates=['purchase_date'])
    df.drop(columns=['created_at'], inplace=True)

    return df

def get_profiles_data():
    response = (
        supabase.table("Profiles")
        .select("*")
        .csv()
        .execute()
    )

    df = pd.read_csv(StringIO(response.data), index_col=0)

    return df


@app.route('/api/data/get_recommendations/<uuid>', methods=['GET'])
def get_data_recommendations(uuid):
    df_payments = get_payments_data()
    df_profiles = get_profiles_data()

    user_profile = df_profiles[df_profiles['uuid'] == uuid]
    gender = user_profile['gender'].values[0]
    age = user_profile['age'].values[0]
    salary = user_profile['salary'].values[0]

    print(gender, age, salary)

    if user_profile.empty:
        return jsonify({"error": "User profile not found"}), 404

get_data_recommendations("47823327-2b0f-48c8-9513-614c3ab5d61a")

@app.route('/api/data/get-u-tags/<uuid>', methods=['GET'])
def get_data_unique_tags(uuid):
    df = get_payments_data()
    unique_tags = df[df['uuid'] == uuid]['tags'].str.strip('{}').str.split(',').explode().unique().tolist()
    return jsonify(unique_tags)

@app.route('/api/data/price-quantity/line-chart/<uuid>', methods=['GET'])
def get_data_price_quantity_line_chart(uuid):
    # Получение параметров start_date и end_date из запроса
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    df = get_payments_data()
    # df = df[df['uuid'] == uuid][['product_name', 'quantity', 'price', 'purchase_date']].drop_duplicates(keep='first')

    df = df[df['uuid'] == uuid][['quantity', 'price', 'tags', 'purchase_date']].drop_duplicates(keep='first')
    df['tags'] = df['tags'].str.strip('{}').str.split(',')
    df = df.explode('tags')

    # Фильтрация по диапазону дат, если параметры указаны
    if start_date and end_date:
        df = df[(df['purchase_date'] >= start_date) & (df['purchase_date'] <= end_date)]

    tmp = df.groupby(['tags', 'purchase_date']).sum().reset_index().sort_values(by='purchase_date')

    # Уникальные даты
    labels = tmp['purchase_date'].astype(str).unique().tolist()

    # Подготовка данных для Quantity
    quantity_datasets = []
    for i, (product_name, group) in enumerate(tmp.groupby('tags')):
        color = caramel_latte_palette[i % len(caramel_latte_palette)]
        quantity_datasets.append({
            "label": product_name,
            "data": group.set_index('purchase_date')['quantity'].reindex(labels, fill_value=0).tolist(),
            "backgroundColor": color["backgroundColor"],
            "borderColor": color["borderColor"],
            "fill": False
        })

    # Подготовка данных для Price
    price_datasets = []
    for i, (product_name, group) in enumerate(tmp.groupby('tags')):
        color = caramel_latte_palette[i % len(caramel_latte_palette)]
        price_datasets.append({
            "label": product_name,
            "data": group.set_index('purchase_date')['price'].reindex(labels, fill_value=0).tolist(),
            "backgroundColor": color["backgroundColor"],
            "borderColor": color["borderColor"],
            "fill": False
        })

    # Формирование JSON
    chart_data = {
        "quantity": {
            "labels": labels,
            "datasets": quantity_datasets
        },
        "price": {
            "labels": labels,
            "datasets": price_datasets
        }
    }

    return jsonify(chart_data)

@app.route('/api/data/tag/price-quantity/line-chart/<uuid>', methods=['GET'])
def get_tag_price_quantity_line_chart(uuid):
    # Получение параметров start_date, end_date и tag из запроса
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    tag = request.args.get('tag')

    if not tag:
        return jsonify({"error": "Tag parameter is required"}), 400

    df = get_payments_data()
    df = df[df['uuid'] == uuid][['quantity', 'price', 'tags', 'purchase_date']].drop_duplicates(keep='first')
    df['tags'] = df['tags'].str.strip('{}').str.split(',')
    df = df.explode('tags')
    df = df[df['tags'] == tag].drop('tags', axis=1)

    # Фильтрация по диапазону дат, если параметры указаны
    if start_date and end_date:
        df = df[(df['purchase_date'] >= start_date) & (df['purchase_date'] <= end_date)]

    # Группировка по дате и суммирование
    tmp = df.groupby('purchase_date').sum().reset_index().sort_values(by='purchase_date')

    # Уникальные даты
    labels = tmp['purchase_date'].astype(str).unique().tolist()

    # Подготовка данных для Quantity
    quantity_dataset = {
        "label": f"Quantity ({tag})",
        "data": tmp['quantity'].tolist(),
        "backgroundColor": caramel_latte_palette[0]["backgroundColor"],
        "borderColor": caramel_latte_palette[0]["borderColor"],
        "fill": False
    }

    # Подготовка данных для Price
    price_dataset = {
        "label": f"Price ({tag})",
        "data": tmp['price'].tolist(),
        "backgroundColor": caramel_latte_palette[1]["backgroundColor"],
        "borderColor": caramel_latte_palette[1]["borderColor"],
        "fill": False
    }

    # Формирование JSON
    chart_data = {
        "quantity": {
            "labels": labels,
            "datasets": [quantity_dataset]
        },
        "price": {
            "labels": labels,
            "datasets": [price_dataset]
        }
    }

    return jsonify(chart_data)


@app.route('/api/data/price-quantity/pie-chart/<uuid>', methods=['GET'])
def get_data_price_quantity_pie_chart(uuid):
    # Получение параметров start_date и end_date из запроса
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    df = get_payments_data()

    df = df[df['uuid'] == uuid][['quantity', 'price', 'tags', 'purchase_date']]
    df['tags'] = df['tags'].str.strip('{}').str.split(',')
    df = df.explode('tags')

    # Фильтрация по диапазону дат, если параметры указаны
    if start_date and end_date:
        df = df[(df['purchase_date'] >= start_date) & (df['purchase_date'] <= end_date)]

    # Группировка по тегам и суммирование
    grouped = df.groupby('tags').agg({'quantity': 'sum', 'price': 'sum'}).reset_index()

    # Подготовка данных для Chart.js
    labels = grouped['tags'].tolist()
    
    # Данные для Quantity pie chart
    quantity_dataset = {
        "data": grouped['quantity'].tolist(),
        "backgroundColor": [caramel_latte_palette[i % len(caramel_latte_palette)]["backgroundColor"] for i in range(len(labels))],
        "borderColor": [caramel_latte_palette[i % len(caramel_latte_palette)]["borderColor"] for i in range(len(labels))]
    }

    # Данные для Price pie chart
    price_dataset = {
        "data": grouped['price'].tolist(),
        "backgroundColor": [caramel_latte_palette[i % len(caramel_latte_palette)]["backgroundColor"] for i in range(len(labels))],
        "borderColor": [caramel_latte_palette[i % len(caramel_latte_palette)]["borderColor"] for i in range(len(labels))]
    }

    # Формирование JSON
    chart_data = {
        "quantity": {
            "labels": labels,
            "datasets": [quantity_dataset]
        },
        "price": {
            "labels": labels,
            "datasets": [price_dataset]
        }
    }

    return jsonify(chart_data)

@app.route('/api/data/price-general/line-chart/<uuid>', methods=['GET'])
def get_data_price_general_line_chart(uuid):
    # Получение параметров start_date и end_date из запроса
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    df = get_payments_data()

    df = df[df['uuid'] == uuid][['price', 'purchase_date']]

    # Фильтрация по диапазону дат, если параметры указаны
    if start_date and end_date:
        df = df[(df['purchase_date'] >= start_date) & (df['purchase_date'] <= end_date)]

    # Группировка по дате и суммирование цен
    grouped = df.groupby('purchase_date').sum().reset_index().sort_values(by='purchase_date')

    # Уникальные даты для меток
    labels = grouped['purchase_date'].astype(str).tolist()

    # Подготовка данных для Price
    price_dataset = {
        "label": "Total Price",
        "data": grouped['price'].tolist(),
        "backgroundColor": caramel_latte_palette[0]["backgroundColor"],
        "borderColor": caramel_latte_palette[0]["borderColor"],
        "fill": False
    }

    # Формирование JSON
    chart_data = {
        "price": {
            "labels": labels,
            "datasets": [price_dataset]
        }
    }

    return jsonify(chart_data)

@app.route('/api/yandex_gpt/<uuid>', methods=['GET'])
def get_yandex_gpt(uuid):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    try:
        df_payments = get_payments_data()
        df_profiles = get_profiles_data()

        # Проверяем профиль, но не прерываем выполнение, если он не найден
        user_profile = df_profiles[df_profiles['uuid'] == uuid]
        salary = None
        if not user_profile.empty:
            salary = user_profile['salary'].values[0]

        df_payments = df_payments[df_payments['uuid'] == uuid][['quantity', 'price', 'tags', 'purchase_date']]
        df_payments['tags'] = df_payments['tags'].str.strip('{}').str.split(',')
        df_payments = df_payments.explode('tags')

        if start_date and end_date:
            df_payments = df_payments[(df_payments['purchase_date'] >= start_date) & (df_payments['purchase_date'] <= end_date)]

        # Группировка по тегам и датам
        grouped = df_payments.groupby(['tags', 'purchase_date']).sum().reset_index()

        # Проверяем, есть ли данные для анализа
        if grouped.empty:
            return jsonify({"error": "Нет данных для анализа за указанный период"}), 404

        # Формируем текстовое описание для GPT
        summary = "Анализируй следующие данные о покупках:\n"
        # Добавляем зарплату только если профиль найден и зарплата валидна
        if pd.notna(salary) and isinstance(salary, (int, float)) and salary > 0:
            summary += f"Зарплата пользователя: {salary} руб.\n\n"
        # Данные о покупках
        summary += "Данные о покупках:\n"
        for _, row in grouped.iterrows():
            summary += f"Тег: {row['tags']}, Дата: {row['purchase_date']}, Количество: {row['quantity']}, Цена: {row['price']} руб.\n"

        # Отправляем запрос в Yandex GPT
        gpt_response = yandexGPT.send_request(summary)

        # Возвращаем результат
        return jsonify({
            "analysis": gpt_response
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# const text = "Hello world! How are you?";
# const url = `http://localhost:5000/api/yandex_gpt?text=${encodeURIComponent(text)}`;

# fetch(url)
#   .then(response => response.json())
#   .then(data => console.log(data))
#   .catch(error => console.error('Error:', error));


if __name__ == '__main__':
    app.run(debug=True)