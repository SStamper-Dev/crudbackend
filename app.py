import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

# load config
app = Flask(__name__)
CORS(app) 

# connection function
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306))
    )

@app.route('/test', methods=['POST'])
def test_no_sql():
    return jsonify({"message": "The wire is working! Python is alive."}), 200

@app.route('/add-pizza', methods=['POST'])
def add_pizza_order():
    db = None
    try:
        data = request.json # this expects {crust, size, order_type, toppings: [id1, id2]}
        db = get_db_connection()
        cursor = db.cursor()

        # insert into the 'pizza' table (matches your new DDL)
        pizza_sql = "INSERT INTO pizza (crust, size, order_type) VALUES (%s, %s, %s)"
        cursor.execute(pizza_sql, (data['crust'], data['size'], data['order_type']))
        
        # Get the ID of the pizza we just created to link toppings
        pizza_id = cursor.lastrowid 

        # insert into the 'pizza_topping' junction table
        if 'toppings' in data and data['toppings']:
            topping_sql = "INSERT INTO pizza_topping (pizza_id, topping_id) VALUES (%s, %s)"
            # creates link for every topping selected
            topping_data = [(pizza_id, t_id) for t_id in data['toppings']]
            cursor.executemany(topping_sql, topping_data)

        db.commit()
        cursor.close()
        return jsonify({"message": f"Pizza #{pizza_id} recorded!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if db:
            db.close()