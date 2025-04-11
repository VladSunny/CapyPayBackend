from flask import Flask, jsonify, request
import os
from supabase import create_client, Client
from io import StringIO
import pandas as pd

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(supabase_url, supabase_key)

app = Flask(__name__)

def get_data():
    response = (
        supabase.table("Payments")
        .select("*")
        .csv()
        .execute()
    )

    df = pd.read_csv(StringIO(response.data), index_col=0)
    df.drop(columns=['created_at'], inplace=True)

    return df

@app.route('/api/data/price-quantity/<uuid>', methods=['GET'])
def get_data_price_quantity(uuid):
    df = get_data()
    df = df[df['uuid'] == uuid][['product_name', 'quantity', 'price', 'purchase_date']]

    tmp = df.groupby(['product_name', 'purchase_date']).sum().reset_index()

    # Уникальные даты
    labels = tmp['purchase_date'].unique().tolist()

    # Подготовка данных для Quantity
    quantity_datasets = []
    for product_name, group in tmp.groupby('product_name'):
        quantity_datasets.append({
            "label": product_name,
            "data": group.set_index('purchase_date')['quantity'].reindex(labels, fill_value=0).tolist()
        })

    # Подготовка данных для Price
    price_datasets = []
    for product_name, group in tmp.groupby('product_name'):
        price_datasets.append({
            "label": product_name,
            "data": group.set_index('purchase_date')['price'].reindex(labels, fill_value=0).tolist()
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