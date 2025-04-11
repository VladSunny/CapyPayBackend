from flask import Flask, jsonify, request

app = Flask(__name__)

# Пример данных (можно заменить на базу данных)
data_store = {
    "message": "Hello from Flask backend!",
    "items": ["Item 1", "Item 2", "Item 3"]
}

# GET-запрос для получения данных
@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(data_store)

# POST-запрос для добавления нового элемента
@app.route('/api/data', methods=['POST'])
def add_item():
    new_item = request.json.get('item')
    if new_item:
        data_store['items'].append(new_item)
        return jsonify({"status": "success", "message": f"Added {new_item}"}), 201
    return jsonify({"status": "error", "message": "No item provided"}), 400

if __name__ == '__main__':
    app.run(debug=True)