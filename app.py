import os
from dotenv import load_dotenv
from flask_cors import CORS

from flask import Flask, request, jsonify
import mysql.connector

# Database Connection
load_dotenv()
app = Flask(__name__)
CORS(app)  # This tells the server it's okay to accept requests from your Netlify domain.

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_NAME")
)

@app.route('/add', methods=['POST'])
def add_order():
    data = request.json
    cursor = db.cursor()
    # SQL query to "surgically" insert data
    sql = "INSERT INTO orders (customer_name, pizza_size) VALUES (%s, %s)"
    cursor.execute(sql, (data['name'], data['size']))
    db.commit() # This "persists" the data to the disk
    return jsonify({"message": "Order added to SQL!"})

if __name__ == '__main__':
    app.run(debug=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)