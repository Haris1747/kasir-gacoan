#!/usr/bin/env python3
"""
KASIR GACOAN - SISTEM POS SEDERHANA
Enhanced with Receipt Printing Functionality, Database Integration, and User Management
"""
import os
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, flash
import json
from datetime import datetime
from receipt_generator import ReceiptGenerator
from models import db, Product, Transaction, TransactionItem, User
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "gacoan_pos_secret_key_2024")

# Database configuration
database_url = os.environ.get("DATABASE_URL")
if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
else:
    # Fallback for development
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kasir_gacoan.db"

db.init_app(app)

# Stock alerts threshold
STOCK_ALERT_THRESHOLD = 10

# Valid categories (removed 'main' and 'appetizer')
VALID_CATEGORIES = ['makanan', 'snack', 'minuman']

# Initialize database and default data
def init_database():
    """Initialize database with tables and default data"""
    with app.app_context():
        db.create_all()
        
        # Check if users exist, if not create default users
        if User.query.count() == 0:
            default_users = [
                User(username='Haris', password_hash=generate_password_hash('110405'), role='cashier'),
                User(username='Dhini', password_hash=generate_password_hash('Riantina'), role='cashier'),
                User(username='Susanto', password_hash=generate_password_hash('Santo'), role='cashier'),
                User(username='Tribudi', password_hash=generate_password_hash('Prasetyo'), role='cashier'),
                User(username='Adinda', password_hash=generate_password_hash('Putri'), role='admin')
            ]
            for user in default_users:
                db.session.add(user)
            db.session.commit()
            logging.info("Default users created")
        
        # Check if products exist, if not create default products
        if Product.query.count() == 0:
            default_products = [
                Product(name='Gacoan Level 1', price=10000, stock=100, category='makanan'),
                Product(name='Gacoan Level 2', price=10000, stock=100, category='makanan'),
                Product(name='Gacoan Level 3', price=10000, stock=100, category='makanan'),
                Product(name='Gacoan Level 4', price=10000, stock=100, category='makanan'),
                Product(name='Gacoan Level 5', price=12000, stock=100, category='makanan'),
                Product(name='Gacoan Level 6', price=16000, stock=100, category='makanan'),
                Product(name='Gacoan Level 7', price=17000, stock=100, category='makanan'),
                Product(name='Gacoan Level 8', price=18000, stock=100, category='makanan'),
                Product(name='Udang Keju', price=10000, stock=50, category='snack'),
                Product(name='Udang Rambutan', price=12000, stock=50, category='snack'),
                Product(name='Lumpia Udang', price=11000, stock=50, category='snack'),
                Product(name='Dimsum Ayam', price=15000, stock=30, category='snack'),
                Product(name='Pangsit Goreng', price=13000, stock=40, category='snack'),
                Product(name='Es Teh Manis', price=5000, stock=100, category='minuman'),
                Product(name='Es Jeruk', price=6000, stock=100, category='minuman'),
                Product(name='Kopi Hitam', price=8000, stock=80, category='minuman'),
                Product(name='Jus Alpukat', price=12000, stock=50, category='minuman')
            ]
            for product in default_products:
                db.session.add(product)
            db.session.commit()
            logging.info("Default products created")

def format_currency(amount):
    """Format currency to Indonesian Rupiah format"""
    return f"Rp {amount:,}".replace(",", ".")

def generate_transaction_id():
    """Generate unique transaction ID"""
    return f"TRX-{int(datetime.now().timestamp())}"

def get_low_stock_products():
    """Get products with low stock"""
    return Product.query.filter(Product.stock <= STOCK_ALERT_THRESHOLD).all()

def require_login(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def require_admin(f):
    """Decorator to require admin role for routes"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=session['username']).first()
        if not user or user.role != 'admin':
            flash('Akses ditolak. Hanya admin yang dapat mengakses halaman ini.', 'error')
            return redirect(url_for('pos'))
        return f(*args, **kwargs)
    return wrapper

@app.route('/')
def index():
    """Redirect to POS if logged in, otherwise to login"""
    if 'username' in session:
        return redirect(url_for('pos'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username, is_active=True).first()
        if user and check_password_hash(user.password_hash, password):
            session['username'] = username
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['login_time'] = datetime.now().isoformat()
            flash('Login berhasil!', 'success')
            return redirect(url_for('pos'))
        else:
            flash('Username atau password salah!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@require_login
def logout():
    """Handle user logout"""
    session.clear()
    flash('Logout berhasil!', 'success')
    return redirect(url_for('login'))

@app.route('/change-password', methods=['GET', 'POST'])
@require_login
def change_password():
    """Handle password change for current user"""
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        user = User.query.filter_by(username=session['username']).first()
        
        if not check_password_hash(user.password_hash, current_password):
            flash('Password lama salah!', 'error')
        elif new_password != confirm_password:
            flash('Password baru dan konfirmasi password tidak sama!', 'error')
        elif len(new_password) < 4:
            flash('Password minimal 4 karakter!', 'error')
        else:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Password berhasil diubah!', 'success')
            return redirect(url_for('pos'))
    
    return render_template('change_password.html')

@app.route('/pos')
@require_login
def pos():
    """Main POS interface"""
    products = Product.query.all()
    low_stock = get_low_stock_products()
    return render_template('pos.html', 
                         products=products, 
                         format_currency=format_currency,
                         low_stock=low_stock)

@app.route('/api/products')
@require_login
def api_products():
    """API endpoint to get products"""
    category = request.args.get('category')
    if category and category != 'all':
        products = Product.query.filter_by(category=category).all()
    else:
        products = Product.query.all()
    return jsonify([p.to_dict() for p in products])

@app.route('/api/checkout', methods=['POST'])
@require_login
def api_checkout():
    """Process checkout and create transaction"""
    try:
        data = request.get_json()
        cart_items = data.get('cart_items', [])
        payment_amount = data.get('payment_amount', 0)
        
        if not cart_items:
            return jsonify({'success': False, 'message': 'Keranjang kosong'}), 400
        
        # Calculate totals
        subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
        discount = 0
        if subtotal >= 100000:  # 10% discount for orders >= 100k
            discount = subtotal * 0.1
        
        total = subtotal - discount
        
        if payment_amount < total:
            return jsonify({'success': False, 'message': 'Pembayaran kurang'}), 400
        
        change = payment_amount - total
        
        # Create transaction
        transaction = {
            'id': generate_transaction_id(),
            'date': datetime.now().isoformat(),
            'cashier': session['username'],
            'items': cart_items,
            'subtotal': subtotal,
            'discount': discount,
            'total': total,
            'payment': payment_amount,
            'change': change
        }
        
        # Create transaction record
        new_transaction = Transaction(
            id=transaction['id'],
            date=datetime.now(),
            cashier=session['username'],
            subtotal=subtotal,
            discount=discount,
            total=total,
            payment=payment_amount,
            change=change
        )
        db.session.add(new_transaction)
        
        # Create transaction items and update stock immediately
        for cart_item in cart_items:
            # Update product stock first (before creating transaction item)
            product = Product.query.get(cart_item['id'])
            if product:
                if product.stock < cart_item['quantity']:
                    return jsonify({'success': False, 'message': f'Stok {product.name} tidak mencukupi'}), 400
                product.stock -= cart_item['quantity']
            
            # Create transaction item
            transaction_item = TransactionItem(
                transaction_id=transaction['id'],
                product_id=cart_item['id'],
                product_name=cart_item['name'],
                price=cart_item['price'],
                quantity=cart_item['quantity'],
                subtotal=cart_item['price'] * cart_item['quantity']
            )
            db.session.add(transaction_item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'transaction_id': transaction['id'],
            'total': total,
            'payment': payment_amount,
            'change': change
        })
        
    except Exception as e:
        logging.error(f"Checkout error: {str(e)}")
        return jsonify({'success': False, 'message': 'Terjadi kesalahan sistem'}), 500

@app.route('/receipt/preview/<transaction_id>')
@require_login
def receipt_preview(transaction_id):
    """Show receipt preview"""
    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        flash('Transaksi tidak ditemukan', 'error')
        return redirect(url_for('pos'))
    
    return render_template('receipt_preview.html', 
                         transaction=transaction, 
                         format_currency=format_currency)

@app.route('/receipt/pdf/<transaction_id>')
@require_login
def receipt_pdf(transaction_id):
    """Generate and download receipt as PDF"""
    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        flash('Transaksi tidak ditemukan', 'error')
        return redirect(url_for('pos'))
    
    try:
        receipt_generator = ReceiptGenerator()
        pdf_path = receipt_generator.generate_pdf(transaction.to_dict())
        
        return send_file(pdf_path, 
                        as_attachment=True, 
                        download_name=f"receipt_{transaction_id}.pdf",
                        mimetype='application/pdf')
    except Exception as e:
        logging.error(f"PDF generation error: {str(e)}")
        flash('Gagal membuat PDF', 'error')
        return redirect(url_for('pos'))

@app.route('/api/transactions')
@require_login
def api_transactions():
    """API endpoint to get transaction history"""
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    return jsonify([t.to_dict() for t in transactions])

@app.route('/sales-history')
@require_login
def sales_history():
    """Sales history page with analytics"""
    from datetime import date, timedelta
    
    # Get recent transactions
    transactions = Transaction.query.order_by(Transaction.date.desc()).limit(50).all()
    
    # Calculate sales metrics
    today = date.today()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today.replace(day=1)
    
    # Today's sales
    today_sales = db.session.query(func.sum(Transaction.total)).filter(
        func.date(Transaction.date) == today
    ).scalar() or 0
    
    # Yesterday's sales
    yesterday_sales = db.session.query(func.sum(Transaction.total)).filter(
        func.date(Transaction.date) == yesterday
    ).scalar() or 0
    
    # This week's sales
    week_sales = db.session.query(func.sum(Transaction.total)).filter(
        Transaction.date >= week_ago
    ).scalar() or 0
    
    # This month's sales
    month_sales = db.session.query(func.sum(Transaction.total)).filter(
        Transaction.date >= month_ago
    ).scalar() or 0
    
    # Get top selling products
    top_products = db.session.query(
        TransactionItem.product_name,
        func.sum(TransactionItem.quantity).label('total_quantity'),
        func.sum(TransactionItem.subtotal).label('total_revenue')
    ).group_by(TransactionItem.product_name).order_by(
        func.sum(TransactionItem.quantity).desc()
    ).limit(10).all()
    
    # Sales by day for last 7 days
    daily_sales = []
    for i in range(7):
        day = today - timedelta(days=i)
        sales = db.session.query(func.sum(Transaction.total)).filter(
            func.date(Transaction.date) == day
        ).scalar() or 0
        daily_sales.append({
            'date': day.strftime('%d/%m'),
            'sales': sales
        })
    daily_sales.reverse()  # Show oldest to newest
    
    # Sales by hour for today
    hourly_sales = []
    for hour in range(24):
        sales = db.session.query(func.sum(Transaction.total)).filter(
            func.date(Transaction.date) == today,
            func.extract('hour', Transaction.date) == hour
        ).scalar() or 0
        hourly_sales.append({
            'hour': f"{hour:02d}:00",
            'sales': sales
        })
    
    # Category performance
    category_sales = db.session.query(
        Product.category,
        func.sum(TransactionItem.subtotal).label('total_sales'),
        func.sum(TransactionItem.quantity).label('total_quantity')
    ).join(TransactionItem, Product.id == TransactionItem.product_id).group_by(
        Product.category
    ).order_by(func.sum(TransactionItem.subtotal).desc()).all()
    
    return render_template('sales_history.html',
                         transactions=transactions,
                         today_sales=today_sales,
                         yesterday_sales=yesterday_sales,
                         week_sales=week_sales,
                         month_sales=month_sales,
                         top_products=top_products,
                         daily_sales=daily_sales,
                         hourly_sales=hourly_sales,
                         category_sales=category_sales,
                         format_currency=format_currency)

@app.route('/api/sales-chart-data')
@require_login
def api_sales_chart_data():
    """API endpoint for sales chart data"""
    from datetime import date, timedelta
    
    chart_type = request.args.get('type', 'daily')
    
    if chart_type == 'daily':
        # Last 30 days
        data = []
        today = date.today()
        for i in range(30):
            day = today - timedelta(days=i)
            sales = db.session.query(func.sum(Transaction.total)).filter(
                func.date(Transaction.date) == day
            ).scalar() or 0
            data.append({
                'label': day.strftime('%d/%m'),
                'value': sales
            })
        data.reverse()
        
    elif chart_type == 'hourly':
        # Today by hour
        data = []
        today = date.today()
        for hour in range(24):
            sales = db.session.query(func.sum(Transaction.total)).filter(
                func.date(Transaction.date) == today,
                func.extract('hour', Transaction.date) == hour
            ).scalar() or 0
            data.append({
                'label': f"{hour:02d}:00",
                'value': sales
            })
            
    elif chart_type == 'products':
        # Top 10 products
        data = []
        top_products = db.session.query(
            TransactionItem.product_name,
            func.sum(TransactionItem.quantity).label('total_quantity')
        ).group_by(TransactionItem.product_name).order_by(
            func.sum(TransactionItem.quantity).desc()
        ).limit(10).all()
        
        for product in top_products:
            data.append({
                'label': product.product_name,
                'value': product.total_quantity
            })
    else:
        data = []
    
    return jsonify(data)

@app.route('/inventory')
@require_admin
def inventory():
    """Inventory management page"""
    products = Product.query.all()
    low_stock = get_low_stock_products()
    return render_template('inventory.html',
                         products=products,
                         low_stock=low_stock,
                         categories=VALID_CATEGORIES,
                         format_currency=format_currency)

@app.route('/inventory/add', methods=['POST'])
@require_admin
def add_product():
    """Add new product to inventory"""
    try:
        name = request.form['name'].strip()
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        category = request.form['category']
        
        # Validation
        if not name:
            flash('Nama produk tidak boleh kosong', 'error')
            return redirect(url_for('inventory'))
        
        if price <= 0:
            flash('Harga harus lebih dari 0', 'error')
            return redirect(url_for('inventory'))
        
        if stock < 0:
            flash('Stok tidak boleh negatif', 'error')
            return redirect(url_for('inventory'))
        
        if category not in VALID_CATEGORIES:
            flash('Kategori tidak valid', 'error')
            return redirect(url_for('inventory'))
        
        # Check if product already exists
        existing_product = Product.query.filter_by(name=name).first()
        if existing_product:
            flash('Produk dengan nama tersebut sudah ada', 'error')
            return redirect(url_for('inventory'))
        
        # Create new product
        product = Product(
            name=name,
            price=price,
            stock=stock,
            category=category
        )
        db.session.add(product)
        db.session.commit()
        
        flash('Produk berhasil ditambahkan', 'success')
        
    except ValueError:
        flash('Data yang dimasukkan tidak valid', 'error')
    except Exception as e:
        logging.error(f"Add product error: {str(e)}")
        flash('Terjadi kesalahan sistem', 'error')
    
    return redirect(url_for('inventory'))

@app.route('/inventory/edit/<int:product_id>', methods=['GET', 'POST'])
@require_admin
def edit_product(product_id):
    """Edit existing product"""
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            product.name = request.form['name'].strip()
            product.price = float(request.form['price'])
            product.stock = int(request.form['stock'])
            product.category = request.form['category']
            
            # Validation
            if not product.name:
                flash('Nama produk tidak boleh kosong', 'error')
                return render_template('edit_product.html', product=product, categories=VALID_CATEGORIES)
            
            if product.price <= 0:
                flash('Harga harus lebih dari 0', 'error')
                return render_template('edit_product.html', product=product, categories=VALID_CATEGORIES)
            
            if product.stock < 0:
                flash('Stok tidak boleh negatif', 'error')
                return render_template('edit_product.html', product=product, categories=VALID_CATEGORIES)
            
            if product.category not in VALID_CATEGORIES:
                flash('Kategori tidak valid', 'error')
                return render_template('edit_product.html', product=product, categories=VALID_CATEGORIES)
            
            # Check if another product with same name exists
            existing_product = Product.query.filter(Product.name == product.name, Product.id != product_id).first()
            if existing_product:
                flash('Produk dengan nama tersebut sudah ada', 'error')
                return render_template('edit_product.html', product=product, categories=VALID_CATEGORIES)
            
            db.session.commit()
            flash('Produk berhasil diperbarui', 'success')
            return redirect(url_for('inventory'))
            
        except ValueError:
            flash('Data yang dimasukkan tidak valid', 'error')
        except Exception as e:
            logging.error(f"Edit product error: {str(e)}")
            flash('Terjadi kesalahan sistem', 'error')
    
    return render_template('edit_product.html', product=product, categories=VALID_CATEGORIES)

@app.route('/inventory/delete/<int:product_id>', methods=['POST'])
@require_admin
def delete_product(product_id):
    """Delete product from inventory"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # Check if product has been used in transactions
        transaction_items = TransactionItem.query.filter_by(product_id=product_id).first()
        if transaction_items:
            flash('Tidak dapat menghapus produk yang sudah pernah dijual', 'error')
        else:
            db.session.delete(product)
            db.session.commit()
            flash('Produk berhasil dihapus', 'success')
            
    except Exception as e:
        logging.error(f"Delete product error: {str(e)}")
        flash('Terjadi kesalahan sistem', 'error')
    
    return redirect(url_for('inventory'))

@app.route('/inventory/delete-stock/<int:product_id>', methods=['POST'])
@require_admin
def delete_stock(product_id):
    """Delete specific amount of stock from product"""
    try:
        product = Product.query.get_or_404(product_id)
        quantity = int(request.form['quantity'])
        
        if quantity <= 0:
            flash('Jumlah yang dihapus harus lebih dari 0', 'error')
        elif quantity > product.stock:
            flash('Jumlah yang dihapus tidak boleh lebih dari stok tersedia', 'error')
        else:
            product.stock -= quantity
            db.session.commit()
            flash(f'Berhasil menghapus {quantity} stok dari {product.name}', 'success')
            
    except ValueError:
        flash('Jumlah tidak valid', 'error')
    except Exception as e:
        logging.error(f"Delete stock error: {str(e)}")
        flash('Terjadi kesalahan sistem', 'error')
    
    return redirect(url_for('inventory'))

@app.route('/users')
@require_admin
def user_management():
    """User management page"""
    users = User.query.all()
    return render_template('user_management.html', users=users)

@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@require_admin
def edit_user(user_id):
    """Edit user details"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            username = request.form['username'].strip()
            role = request.form['role']
            new_password = request.form.get('new_password', '').strip()
            
            # Validation
            if not username:
                flash('Username tidak boleh kosong', 'error')
                return redirect(url_for('edit_user', user_id=user_id))
            
            if role not in ['admin', 'cashier']:
                flash('Role tidak valid', 'error')
                return redirect(url_for('edit_user', user_id=user_id))
            
            # Check if username already exists (excluding current user)
            existing_user = User.query.filter(User.username == username, User.id != user_id).first()
            if existing_user:
                flash('Username sudah digunakan', 'error')
                return redirect(url_for('edit_user', user_id=user_id))
            
            # Update user data
            user.username = username
            user.role = role
            
            # Update password if provided
            if new_password:
                if len(new_password) < 4:
                    flash('Password minimal 4 karakter', 'error')
                    return redirect(url_for('edit_user', user_id=user_id))
                user.password_hash = generate_password_hash(new_password)
            
            db.session.commit()
            flash('Data user berhasil diubah', 'success')
            return redirect(url_for('user_management'))
            
        except Exception as e:
            logging.error(f"Edit user error: {str(e)}")
            flash('Terjadi kesalahan sistem', 'error')
            return redirect(url_for('edit_user', user_id=user_id))
    
    return render_template('edit_user.html', user=user)

@app.route('/users/add', methods=['POST'])
@require_admin
def add_user():
    """Add new user"""
    try:
        username = request.form['username'].strip()
        password = request.form['password']
        role = request.form['role']
        
        # Validation
        if not username:
            flash('Username tidak boleh kosong', 'error')
            return redirect(url_for('user_management'))
        
        if len(password) < 4:
            flash('Password minimal 4 karakter', 'error')
            return redirect(url_for('user_management'))
        
        if role not in ['admin', 'cashier']:
            flash('Role tidak valid', 'error')
            return redirect(url_for('user_management'))
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username sudah digunakan', 'error')
            return redirect(url_for('user_management'))
        
        # Create new user
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        db.session.commit()
        
        flash('User berhasil ditambahkan', 'success')
        
    except Exception as e:
        logging.error(f"Add user error: {str(e)}")
        flash('Terjadi kesalahan sistem', 'error')
    
    return redirect(url_for('user_management'))

@app.route('/users/toggle/<int:user_id>', methods=['POST'])
@require_admin
def toggle_user_status(user_id):
    """Toggle user active status"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Don't allow deactivating the current admin user
        if user.username == session['username']:
            flash('Tidak dapat menonaktifkan akun sendiri', 'error')
        else:
            user.is_active = not user.is_active
            db.session.commit()
            status = 'diaktifkan' if user.is_active else 'dinonaktifkan'
            flash(f'User {user.username} berhasil {status}', 'success')
            
    except Exception as e:
        logging.error(f"Toggle user status error: {str(e)}")
        flash('Terjadi kesalahan sistem', 'error')
    
    return redirect(url_for('user_management'))

# Template filters
@app.template_filter('currency')
def currency_filter(amount):
    """Template filter for currency formatting"""
    return format_currency(amount)

# Initialize database when module is imported
with app.app_context():
    init_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
