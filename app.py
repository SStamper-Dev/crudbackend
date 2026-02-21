import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

# load config
load_dotenv()
app = Flask(__name__)
CORS(app) 

# connection function
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "alive"}), 200

@app.route('/add', methods=['POST'])
def add_order():
    try:
        data = request.json
        db = get_db_connection() # connects only when request comes in
        cursor = db.cursor()
        sql = "INSERT INTO testorders (customer_name, pizza_size) VALUES (%s, %s)"
        cursor.execute(sql, (data['name'], data['size']))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"message": "Order added to SQL!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# oort binding
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)