from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from supabase import create_client, Client
from io import StringIO
import pandas as pd
from config import caramel_latte_palette
import dotenv

dotenv.load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

print(supabase_key)

supabase: Client = create_client(supabase_url, supabase_key)

app = Flask(__name__)

CORS(app, origins=["http://localhost:5173", "https://capy-pay.netlify.app"])

def get_data():
    response = (
        supabase.table("Payments")
        .select("*")
        .csv()
        .execute()
    )

    df = pd.read_csv(StringIO(response.data), index_col=0, parse_dates=['purchase_date'])
    df.drop(columns=['created_at'], inplace=True)

    return df

@app.route('/api/data/price-quantity/<uuid>', methods=['GET'])
def get_data_price_quantity(uuid):
    df = get_data()
    df = df[df['uuid'] == uuid][['product_name', 'quantity', 'price', 'purchase_date']].drop_duplicates(keep='first')

    tmp = df.groupby(['product_name', 'purchase_date']).sum().reset_index().sort_values(by='purchase_date')

    # Уникальные даты
    labels = tmp['purchase_date'].astype(str).unique().tolist()

    # Подготовка данных для Quantity
    quantity_datasets = []
    for i, (product_name, group) in enumerate(tmp.groupby('product_name')):
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
    for i, (product_name, group) in enumerate(tmp.groupby('product_name')):
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



if __name__ == '__main__':
    app.run(debug=True)