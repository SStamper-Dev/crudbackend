import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

# load config
app = Flask(__name__)
# server allows ANY website to read the JSON
CORS(app, resources={r"/*": {"origins": "*"}})

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

# CREATE
@app.route('/add-pizza', methods=['POST'])
def add_pizza_order():
    db = None
    try:
        data = request.json
        db = get_db_connection()
        cursor = db.cursor()

        # 1. ENUM Match Check: Ensure 'Dine-in' becomes 'Dine-In'
        order_type = data['order_type'].replace('Dine-in', 'Dine-In')

        pizza_sql = "INSERT INTO pizza (crust, size, order_type) VALUES (%s, %s, %s)"
        cursor.execute(pizza_sql, (data['crust'], data['size'], order_type))
        pizza_id = cursor.lastrowid 

        # 2. Convert Topping Names to IDs
        if 'toppings' in data and data['toppings']:
            # Find IDs for names like "Pepperoni"
            format_strings = ','.join(['%s'] * len(data['toppings']))
            cursor.execute(f"SELECT id FROM topping WHERE name IN ({format_strings})", 
                           tuple(data['toppings']))
            topping_ids = [row[0] for row in cursor.fetchall()]

            # Insert links into the junction table
            topping_sql = "INSERT INTO pizza_topping (pizza_id, topping_id) VALUES (%s, %s)"
            topping_data = [(pizza_id, t_id) for t_id in topping_ids]
            cursor.executemany(topping_sql, topping_data)

        db.commit()
        return jsonify({"message": f"Pizza #{pizza_id} recorded!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if db:
            db.close()

# READ
@app.route('/pizzas', methods=['GET'])
def get_pizzas():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True) # Returns data as a dictionary
    
    # use JOIN to get pizza details and associated toppings
    query = """
    SELECT p.*, GROUP_CONCAT(t.name) as topping_names 
    FROM pizza p
    LEFT JOIN pizza_topping pt ON p.id = pt.pizza_id
    LEFT JOIN topping t ON pt.topping_id = t.id
    GROUP BY p.id
    """
    cursor.execute(query)
    pizzas = cursor.fetchall()
    db.close()
    return jsonify(pizzas), 200

# UPDATE
@app.route('/update-pizza/<int:id>', methods=['PUT'])
def update_pizza(id):
    data = request.json
    db = get_db_connection()
    cursor = db.cursor()
    try:
        # 1. Match the ENUM case for 'Dine-In'
        order_type = data['order_type'].replace('Dine-in', 'Dine-In')

        cursor.execute("UPDATE pizza SET crust=%s, size=%s, order_type=%s WHERE id=%s", 
                       (data['crust'], data['size'], order_type, id))
        
        # 2. Wipe old toppings
        cursor.execute("DELETE FROM pizza_topping WHERE pizza_id=%s", (id,))
        
        # 3. Lookup IDs for names sent by the frontend
        if 'toppings' in data and data['toppings']:
            format_strings = ','.join(['%s'] * len(data['toppings']))
            cursor.execute(f"SELECT id FROM topping WHERE name IN ({format_strings})", 
                           tuple(data['toppings']))
            topping_ids = [row[0] for row in cursor.fetchall()]

            topping_sql = "INSERT INTO pizza_topping (pizza_id, topping_id) VALUES (%s, %s)"
            topping_data = [(id, t_id) for t_id in topping_ids]
            cursor.executemany(topping_sql, topping_data)
        
        db.commit()
        return jsonify({"message": "Update successful"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
        
# DELETE
@app.route('/delete-pizza/<int:id>', methods=['DELETE'])
def delete_pizza(id):
    db = get_db_connection()
    cursor = db.cursor()
    # cascade deletes with toppings
    cursor.execute("DELETE FROM pizza WHERE id=%s", (id,))
    db.commit()
    db.close()
    return jsonify({"message": "Pizza deleted"}), 200