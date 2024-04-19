from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import base64
import requests

app = Flask(__name__)

CORS(app)

sqldbname = 'data/shiopdb.db'

# _____PAGES

# Index route
@app.route('/')
def index():
    user = request.args.get('user')
    return render_template('index.html', user=user)

@app.route('/product')
def product():
    user = request.args.get('user')
    response = requests.get('http://localhost:5000/products')
    products = response.json()
    accessory_products = [product for product in products if product['category'] == 'accessory']
    furniture_products = [product for product in products if product['category'] == 'furniture']
    decoration_products = [product for product in products if product['category'] == 'decoration']
    return render_template('product.html', accessory_products=accessory_products, furniture_products=furniture_products, decoration_products=decoration_products, user=user)

@app.route('/product/<int:id>')
def product_detail(id):
    user = request.args.get('user')
    response = requests.get(f'http://localhost:5000/products/{id}')
    product = response.json()
    return render_template('product_detail.html', product=product, user=user)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

# _____API

# Get all products

@app.route('/products', methods=['GET'])
def get_products():
    conn = sqlite3.connect(sqldbname)
    c = conn.cursor()
    c.execute('SELECT * FROM product')
    products = c.fetchall()
    conn.close()

    # Convert the fetched data into a list of dictionaries
    products_list = []
    for product in products:
        product_dict = {
            'product_id': product[0],
            'name': product[1],
            'image': product[2],
            'description': product[3],
            'price': product[4],
            'category': product[5],
            'in_stock': product[6]
        }
        products_list.append(product_dict)

    return jsonify(products_list)

# Get single product

@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    conn = sqlite3.connect(sqldbname)
    c = conn.cursor()
    c.execute('SELECT * FROM product WHERE product_id = ?', (id,))
    product = c.fetchone()
    conn.close()

    # Convert the fetched data into a dictionary
    product_dict = {
        'product_id': product[0],
        'name': product[1],
        'image': product[2],
        'description': product[3],
        'price': product[4],
        'category': product[5],
        'in_stock': product[6]
    }

    return jsonify(product_dict)

# Add product

@app.route('/products', methods=['POST'])
def add_product():
    conn = sqlite3.connect(sqldbname)
    c = conn.cursor()

    # Get image path
    image_path = request.json['image']

    # Ensure category is in its required value
    category = request.json['category']
    if category not in ['accessory', 'furniture', 'decoration']:
        return 'Invalid category', 400

    c.execute('INSERT INTO product (name, image, description, price, category) VALUES (?, ?, ?, ?, ?)', 
              (request.json['name'], image_path, request.json['description'], request.json['price'], category))
    conn.commit()
    conn.close()
    return 'Product added', 201

# Update product

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    conn = sqlite3.connect(sqldbname)
    c = conn.cursor()

    # Check if image is provided
    if 'image' in request.json:
        # Convert image to blob
        image = request.json['image']
        with open(image, 'rb') as file:
            blob_data = base64.b64encode(file.read())
    else:
        blob_data = None

    # Ensure category is in its required value
    category = request.json['category']
    if category not in ['accessory', 'furniture', 'decoration']:
        return 'Invalid category', 400

    # Update product based on provided attributes
    if blob_data is not None:
        c.execute('UPDATE product SET name = ?, image = ?, description = ?, price = ?, category = ?, in_stock = ? WHERE product_id = ?', 
                  (request.json['name'], blob_data, request.json['description'], request.json['price'], category, request.json['in_stock'], id))
    else:
        c.execute('UPDATE product SET name = ?, description = ?, price = ?, category = ?, in_stock = ? WHERE product_id = ?', 
                  (request.json['name'], request.json['description'], request.json['price'], category, request.json['in_stock'], id))

    conn.commit()
    conn.close()
    return 'Product updated', 200

# Delete product
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    conn = sqlite3.connect(sqldbname)
    c = conn.cursor()
    c.execute('DELETE FROM product WHERE product_id = ?', (id,))
    conn.commit()
    conn.close()
    return 'Product deleted', 200

# Get All Accounts
@app.route('/accounts', methods=['GET'])
def get_accounts():
    conn = sqlite3.connect(sqldbname)
    c = conn.cursor()
    c.execute('SELECT * FROM account')
    accounts = c.fetchall()
    conn.close()
    return jsonify(accounts)

# # Handle Login
# @app.route('/login', methods=['POST'])
# def login():
#     conn = sqlite3.connect(sqldbname)
#     c = conn.cursor()
#     c.execute('SELECT * FROM account WHERE username = ? AND password = ?', 
#               (request.json['username'], request.json['password']))
#     user = c.fetchone()
#     conn.close()
#     if user is not None:
#         return 'Login successful', 200
#     else:
#         return 'Login failed', 401
    
# # Handle Register
# @app.route('/register', methods=['POST'])
# def register():
#     conn = sqlite3.connect(sqldbname)
#     c = conn.cursor()
#     c.execute('INSERT INTO account (username, password) VALUES (?, ?)', 
#               (request.json['username'], request.json['password']))
#     conn.commit()
#     conn.close()
#     return 'Register successful', 201



if __name__ == '__main__':
    app.run(debug=True)