from flask import Flask, redirect, request, jsonify, render_template, session, url_for
from flask_cors import CORS
import sqlite3
import base64
import requests
import hashlib

app = Flask(__name__)
app.secret_key = 'manhdo'

CORS(app)

sqldbname = 'data/shiop.db'

# _____PAGES

# Home page
@app.route('/')
def index():
    user = session.get('user', None)
    return render_template('index.html', user=user)

# Product page
@app.route('/product')
def product():
    user = session.get('user', None)
    response = requests.get('http://localhost:5000/products')
    products = response.json()
    accessory_products = [product for product in products if product['category'] == 'accessory']
    furniture_products = [product for product in products if product['category'] == 'furniture']
    decoration_products = [product for product in products if product['category'] == 'decoration']
    return render_template('product.html', accessory_products=accessory_products, furniture_products=furniture_products, decoration_products=decoration_products, user=user)

# Product detail page
@app.route('/product/<int:id>')
def product_detail(id):
    user = session.get('user', None)
    response = requests.get(f'http://localhost:5000/products/{id}')
    product = response.json()
    return render_template('product_detail.html', product=product, user=user)

# Login page
@app.route('/login')
def login():
    return render_template('login.html')

# Register page
@app.route('/register')
def register():
    return render_template('register.html')

# Account page
@app.route('/account')
def account():
    user = session.get('user', None)
    return render_template('account.html', user=user)

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

# Change password
@app.route('/accounts/<int:id>', methods=['PUT'])
def change_password(id):
    conn = sqlite3.connect(sqldbname)
    c = conn.cursor()

    password = request.json['password']
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    c.execute('UPDATE account SET password = ? WHERE id = ?', (password_hash, id))
    conn.commit()
    conn.close()
    return 'Password changed', 200

# # Handle Login
@app.route('/login', methods=['POST'])
def handle_login():
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return 'Missing username or password', 400

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    conn = sqlite3.connect(sqldbname)
    c = conn.cursor()
    c.execute('SELECT * FROM account WHERE username = ? AND password = ?', 
              (username, password_hash))
    user = c.fetchone()
    conn.close()

    if user is not None:
        user = {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'password': user[2],
            # add more fields if needed
        }
        
        session['user'] = user
        return redirect(url_for('index'))
    else:
        return 'Login failed', 401
    
# Handle Register
@app.route('/register', methods=['POST'])
def handle_register():
    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')

    if not username or not password:
        return 'Missing username or password', 400

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    conn = sqlite3.connect(sqldbname)
    c = conn.cursor()

    try:
        c.execute('INSERT INTO account (username, email, password) VALUES (?, ?, ?)', 
                  (username, email, password_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        return 'Username already exists', 400

    conn.close()
    return 'Register successful', 201

# Handle logout
@app.route('/logout')
def handle_logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# Add to cart
@app.route('/cart', methods=['POST'])
def add_to_cart():
    user = session.get('user', None)
    if user is None:
        return 'Unauthorized', 401

    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity')

    conn = sqlite3.connect(sqldbname)
    c = conn.cursor()
    c.execute('INSERT INTO cart (account_id, product_id, quantity) VALUES (?, ?, ?)', 
              (user['id'], product_id, quantity))
    conn.commit()
    conn.close()
    return 'Added to cart', 201

# Add to favorite
@app.route('/favorite', methods=['POST'])
def add_to_favorite():
    user = session.get('user', None)
    if user is None:
        return 'Unauthorized', 401

    product_id = request.json.get('product_id')

    conn = sqlite3.connect(sqldbname)
    c = conn.cursor()
    c.execute('INSERT INTO favorites (account_id, product_id) VALUES (?, ?)', 
              (user['id'], product_id))
    conn.commit()
    conn.close()
    return 'Added to favorite', 201


if __name__ == '__main__':
    app.run(debug=True)