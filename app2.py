from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from config import DB_CONFIG

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # change this in production

# MySQL configurations
app.config['MYSQL_HOST'] = DB_CONFIG['host']
app.config['MYSQL_USER'] = DB_CONFIG['user']
app.config['MYSQL_PASSWORD'] = DB_CONFIG['jacks123']
app.config['MYSQL_DB'] = DB_CONFIG['db']

mysql = MySQL(app)

# -----------------------
# Helper functions
# -----------------------
def get_user_by_name_and_pass(name, password):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE name=%s AND password=%s', (name, password))
    user = cursor.fetchone()
    cursor.close()
    return user

def is_email_or_password_taken(email, password):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE gmail=%s OR password=%s', (email, password))
    result = cursor.fetchone()
    cursor.close()
    return result is not None

# -----------------------
# Public Routes
# -----------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    # Handles login and registration on the same page
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'login':
            name = request.form.get('name_login')
            password = request.form.get('password_login')
            user = get_user_by_name_and_pass(name, password)
            if user:
                session['loggedin'] = True
                session['id'] = user['id']
                session['name'] = user['name']
                flash('Logged in successfully', 'success')
                return redirect(url_for('explore'))
            else:
                # Check if account exists by name
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM users WHERE name=%s', (name,))
                exists = cursor.fetchone()
                cursor.close()
                if not exists:
                    flash('account does not exist', 'danger')
                else:
                    flash('wrong name or password', 'danger')
                return redirect(url_for('index'))
        elif form_type == 'register':
            name = request.form.get('name_reg')
            password = request.form.get('password_reg')
            gmail = request.form.get('gmail_reg')
            if is_email_or_password_taken(gmail, password):
                flash('Account already taken please change either the gmail or password', 'danger')
                return redirect(url_for('index'))
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO users (name, password, gmail) VALUES (%s, %s, %s)', (name, password, gmail))
            mysql.connection.commit()
            cursor.close()
            flash('Registered successfully. Please login.', 'success')
            return redirect(url_for('index'))
    return render_template('index.html')

@app.route('/explore')
def explore():
    # Read-only page that shows accessories, metals, jewels, designs
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM accessories')
    accessories = cur.fetchall()
    cur.execute('SELECT * FROM metals')
    metals = cur.fetchall()
    cur.execute('SELECT * FROM jewels')
    jewels = cur.fetchall()
    cur.execute('SELECT * FROM designs')
    designs = cur.fetchall()
    cur.close()
    return render_template('explore.html', accessories=accessories, metals=metals, jewels=jewels, designs=designs)

@app.route('/order', methods=['GET', 'POST'])
def order():
    if not session.get('loggedin'):
        flash('You are not logged-in please log-in to order', 'warning')
        return redirect(url_for('explore'))
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM accessories')
    accessories = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        # Handles placing orders list of items in JSON
        orders = request.form.get('orders_json')
        # In a real app you'd parse and store orders in an orders table.
        flash('Orders received and recorded (simulated).', 'success')
        return redirect(url_for('explore'))
    return render_template('order.html', accessories=accessories)

@app.route('/profile')
def profile():
    if not session.get('loggedin'):
        flash('You are not logged-in please log-in to view profile', 'warning')
        return redirect(url_for('index'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE id=%s', (session['id'],))
    user = cursor.fetchone()
    cursor.close()
    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('index'))

# -----------------------
# Admin Routes
# -----------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        name = request.form.get('admin_name')
        password = request.form.get('admin_password')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admin WHERE name=%s AND password=%s', (name, password))
        admin = cursor.fetchone()
        cursor.close()
        if admin:
            session['admin_loggedin'] = True
            session['admin_name'] = admin['name']
            flash('Admin logged in', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Admin login failed', 'danger')
    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

# Users CRUD (admin)
@app.route('/admin/users')
def admin_users():
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM users')
    users = cur.fetchall()
    cur.close()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/add', methods=['GET', 'POST'])
def admin_users_add():
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        gmail = request.form.get('gmail')
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO users (name, password, gmail) VALUES (%s,%s,%s)', (name, password, gmail))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('admin_users'))
    return render_template('admin_users_add.html')

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
def admin_users_edit(user_id):
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        gmail = request.form.get('gmail')
        cur2 = mysql.connection.cursor()
        cur2.execute('UPDATE users SET name=%s, password=%s, gmail=%s WHERE id=%s', (name, password, gmail, user_id))
        mysql.connection.commit()
        cur2.close()
        return redirect(url_for('admin_users'))
    cur.execute('SELECT * FROM users WHERE id=%s', (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('admin_users_edit.html', user=user)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def admin_users_delete(user_id):
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM users WHERE id=%s', (user_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin_users'))

# Items CRUD (Accessories/Metals/Jewels/Designs)
def generic_list(table):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(f'SELECT * FROM {table}')
    rows = cur.fetchall()
    cur.close()
    return rows

@app.route('/admin/items')
def admin_items():
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    return render_template('admin_items.html')

# Accessories
@app.route('/admin/items/accessories')
def admin_accessories():
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    accessories = generic_list('accessories')
    return render_template('admin_accessories.html', accessories=accessories)

@app.route('/admin/items/accessories/add', methods=['GET', 'POST'])
def admin_accessories_add():
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO accessories (name, price) VALUES (%s,%s)', (name, price))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('admin_accessories'))
    return render_template('admin_accessories_add.html')

@app.route('/admin/items/accessories/edit/<int:item_id>', methods=['GET', 'POST'])
def admin_accessories_edit(item_id):
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        cur2 = mysql.connection.cursor()
        cur2.execute('UPDATE accessories SET name=%s, price=%s WHERE id=%s', (name, price, item_id))
        mysql.connection.commit()
        cur2.close()
        return redirect(url_for('admin_accessories'))
    cur.execute('SELECT * FROM accessories WHERE id=%s', (item_id,))
    item = cur.fetchone()
    cur.close()
    return render_template('admin_accessories_edit.html', item=item)

@app.route('/admin/items/accessories/delete/<int:item_id>', methods=['POST'])
def admin_accessories_delete(item_id):
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM accessories WHERE id=%s', (item_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin_accessories'))

# Metals
@app.route('/admin/items/metals')
def admin_metals():
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    metals = generic_list('metals')
    return render_template('admin_metals.html', metals=metals)

@app.route('/admin/items/metals/add', methods=['GET', 'POST'])
def admin_metals_add():
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO metals (name, price) VALUES (%s,%s)', (name, price))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('admin_metals'))
    return render_template('admin_metals_add.html')

@app.route('/admin/items/metals/edit/<int:item_id>', methods=['GET', 'POST'])
def admin_metals_edit(item_id):
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        cur2 = mysql.connection.cursor()
        cur2.execute('UPDATE metals SET name=%s, price=%s WHERE id=%s', (name, price, item_id))
        mysql.connection.commit()
        cur2.close()
        return redirect(url_for('admin_metals'))
    cur.execute('SELECT * FROM metals WHERE id=%s', (item_id,))
    item = cur.fetchone()
    cur.close()
    return render_template('admin_metals_edit.html', item=item)

@app.route('/admin/items/metals/delete/<int:item_id>', methods=['POST'])
def admin_metals_delete(item_id):
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM metals WHERE id=%s', (item_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin_metals'))

# Jewels
@app.route('/admin/items/jewels')
def admin_jewels():
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    jewels = generic_list('jewels')
    return render_template('admin_jewels.html', jewels=jewels)

@app.route('/admin/items/jewels/add', methods=['GET', 'POST'])
def admin_jewels_add():
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO jewels (name, price) VALUES (%s,%s)', (name, price))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('admin_jewels'))
    return render_template('admin_jewels_add.html')

@app.route('/admin/items/jewels/edit/<int:item_id>', methods=['GET', 'POST'])
def admin_jewels_edit(item_id):
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        cur2 = mysql.connection.cursor()
        cur2.execute('UPDATE jewels SET name=%s, price=%s WHERE id=%s', (name, price, item_id))
        mysql.connection.commit()
        cur2.close()
        return redirect(url_for('admin_jewels'))
    cur.execute('SELECT * FROM jewels WHERE id=%s', (item_id,))
    item = cur.fetchone()
    cur.close()
    return render_template('admin_jewels_edit.html', item=item)

@app.route('/admin/items/jewels/delete/<int:item_id>', methods=['POST'])
def admin_jewels_delete(item_id):
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM jewels WHERE id=%s', (item_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin_jewels'))

# Designs
@app.route('/admin/items/designs')
def admin_designs():
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    designs = generic_list('designs')
    return render_template('admin_designs.html', designs=designs)

@app.route('/admin/items/designs/add', methods=['GET', 'POST'])
def admin_designs_add():
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO designs (name, price) VALUES (%s,%s)', (name, price))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('admin_designs'))
    return render_template('admin_designs_add.html')

@app.route('/admin/items/designs/edit/<int:item_id>', methods=['GET', 'POST'])
def admin_designs_edit(item_id):
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        cur2 = mysql.connection.cursor()
        cur2.execute('UPDATE designs SET name=%s, price=%s WHERE id=%s', (name, price, item_id))
        mysql.connection.commit()
        cur2.close()
        return redirect(url_for('admin_designs'))
    cur.execute('SELECT * FROM designs WHERE id=%s', (item_id,))
    item = cur.fetchone()
    cur.close()
    return render_template('admin_designs_edit.html', item=item)

@app.route('/admin/items/designs/delete/<int:item_id>', methods=['POST'])
def admin_designs_delete(item_id):
    if not session.get('admin_loggedin'):
        return redirect(url_for('admin_login'))
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM designs WHERE id=%s', (item_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin_designs'))

if __name__ == '__main__':
    app.run(debug=True)
