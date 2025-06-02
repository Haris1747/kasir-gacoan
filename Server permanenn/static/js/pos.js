// POS JavaScript functionality
class POSSystem {
    constructor() {
        this.cart = [];
        this.products = [];
        this.currentCategory = 'all';
        this.init();
    }

    init() {
        this.loadProducts();
        this.bindEvents();
        this.updateCartDisplay();
    }

    loadProducts() {
        // Products are already loaded in the template
        // This method can be extended for dynamic loading if needed
        this.bindProductEvents();
    }

    bindEvents() {
        // Category filter events
        document.querySelectorAll('input[name="category"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.filterProducts(e.target.value);
            });
        });

        // Payment amount input
        const paymentInput = document.getElementById('payment-amount');
        if (paymentInput) {
            paymentInput.addEventListener('input', () => {
                this.calculateChange();
            });
        }

        // Checkout button
        const checkoutBtn = document.getElementById('checkout-btn');
        if (checkoutBtn) {
            checkoutBtn.addEventListener('click', () => {
                this.processCheckout();
            });
        }

        // Clear cart button
        const clearCartBtn = document.getElementById('clear-cart-btn');
        if (clearCartBtn) {
            clearCartBtn.addEventListener('click', () => {
                this.clearCart();
            });
        }
    }

    bindProductEvents() {
        // Add to cart buttons
        document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const productCard = e.target.closest('.product-card');
                this.addToCart(productCard);
            });
        });
    }

    filterProducts(category) {
        this.currentCategory = category;
        const productItems = document.querySelectorAll('.product-item');
        
        productItems.forEach(item => {
            if (category === 'all' || item.dataset.category === category) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }

    addToCart(productCard) {
        const productId = parseInt(productCard.dataset.productId);
        const productName = productCard.dataset.productName;
        const productPrice = parseFloat(productCard.dataset.productPrice);
        const productStock = parseInt(productCard.dataset.productStock);

        if (productStock <= 0) {
            this.showAlert('Produk habis!', 'warning');
            return;
        }

        // Check if product already in cart
        const existingItem = this.cart.find(item => item.id === productId);
        
        if (existingItem) {
            if (existingItem.quantity >= productStock) {
                this.showAlert('Tidak dapat menambah lebih dari stok tersedia!', 'warning');
                return;
            }
            existingItem.quantity += 1;
        } else {
            this.cart.push({
                id: productId,
                name: productName,
                price: productPrice,
                quantity: 1,
                stock: productStock
            });
        }

        // Animation effect
        productCard.classList.add('add-to-cart-animation');
        setTimeout(() => {
            productCard.classList.remove('add-to-cart-animation');
        }, 300);

        this.updateCartDisplay();
        this.showAlert(`${productName} ditambahkan ke keranjang`, 'success');
    }

    removeFromCart(productId) {
        this.cart = this.cart.filter(item => item.id !== productId);
        this.updateCartDisplay();
    }

    updateQuantity(productId, newQuantity) {
        const item = this.cart.find(item => item.id === productId);
        if (item) {
            if (newQuantity <= 0) {
                this.removeFromCart(productId);
            } else if (newQuantity <= item.stock) {
                item.quantity = newQuantity;
                this.updateCartDisplay();
            } else {
                this.showAlert('Quantity tidak boleh lebih dari stok tersedia!', 'warning');
            }
        }
    }

    updateCartDisplay() {
        const cartItemsContainer = document.getElementById('cart-items');
        const cartSummary = document.getElementById('cart-summary');

        if (this.cart.length === 0) {
            cartItemsContainer.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-shopping-bag fa-2x mb-2"></i>
                    <p>Keranjang masih kosong</p>
                </div>
            `;
            cartSummary.style.display = 'none';
        } else {
            // Render cart items
            cartItemsContainer.innerHTML = this.cart.map(item => `
                <div class="cart-item">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h6 class="mb-1">${item.name}</h6>
                            <small class="text-muted">${this.formatCurrency(item.price)} × ${item.quantity}</small>
                        </div>
                        <div class="text-end">
                            <strong>${this.formatCurrency(item.price * item.quantity)}</strong>
                        </div>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mt-2">
                        <div class="cart-item-controls">
                            <button class="btn btn-sm btn-outline-secondary" onclick="pos.updateQuantity(${item.id}, ${item.quantity - 1})">
                                <i class="fas fa-minus"></i>
                            </button>
                            <input type="number" class="form-control form-control-sm quantity-control" 
                                   value="${item.quantity}" min="1" max="${item.stock}"
                                   onchange="pos.updateQuantity(${item.id}, parseInt(this.value))">
                            <button class="btn btn-sm btn-outline-secondary" onclick="pos.updateQuantity(${item.id}, ${item.quantity + 1})">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                        <button class="btn btn-sm btn-outline-danger" onclick="pos.removeFromCart(${item.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('');

            // Show cart summary
            cartSummary.style.display = 'block';
            this.updateCartSummary();
        }
    }

    updateCartSummary() {
        const subtotal = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        const discount = subtotal >= 100000 ? subtotal * 0.1 : 0;
        const total = subtotal - discount;

        document.getElementById('subtotal').textContent = this.formatCurrency(subtotal);
        document.getElementById('total').textContent = this.formatCurrency(total);

        // Show/hide discount row
        const discountRow = document.getElementById('discount-row');
        if (discount > 0) {
            discountRow.style.display = 'flex';
            document.getElementById('discount').textContent = `-${this.formatCurrency(discount)}`;
        } else {
            discountRow.style.display = 'none';
        }

        this.calculateChange();
    }

    calculateChange() {
        const paymentInput = document.getElementById('payment-amount');
        const changeElement = document.getElementById('change');
        const changeRow = document.getElementById('change-row');
        const checkoutBtn = document.getElementById('checkout-btn');

        if (!paymentInput || !changeElement || !checkoutBtn) return;

        const subtotal = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        const discount = subtotal >= 100000 ? subtotal * 0.1 : 0;
        const total = subtotal - discount;
        const payment = parseFloat(paymentInput.value) || 0;
        const change = payment - total;

        if (payment > 0) {
            changeRow.style.display = 'flex';
            changeElement.textContent = this.formatCurrency(Math.max(0, change));
            changeElement.className = change >= 0 ? 'text-success' : 'text-danger';
        } else {
            changeRow.style.display = 'none';
        }

        // Enable/disable checkout button
        checkoutBtn.disabled = payment < total || this.cart.length === 0;
    }

    async processCheckout() {
        if (this.cart.length === 0) {
            this.showAlert('Keranjang kosong!', 'warning');
            return;
        }

        const paymentAmount = parseFloat(document.getElementById('payment-amount').value) || 0;
        const subtotal = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        const discount = subtotal >= 100000 ? subtotal * 0.1 : 0;
        const total = subtotal - discount;

        if (paymentAmount < total) {
            this.showAlert('Jumlah pembayaran kurang!', 'warning');
            return;
        }

        // Show loading
        const checkoutBtn = document.getElementById('checkout-btn');
        const originalText = checkoutBtn.innerHTML;
        checkoutBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Memproses...';
        checkoutBtn.disabled = true;

        try {
            const response = await fetch('/api/checkout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    cart_items: this.cart,
                    payment_amount: paymentAmount
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showReceiptModal(result);
                this.updateProductStock();
                this.clearCart();
            } else {
                this.showAlert(result.message || 'Checkout gagal!', 'danger');
            }
        } catch (error) {
            console.error('Checkout error:', error);
            this.showAlert('Terjadi kesalahan sistem!', 'danger');
        } finally {
            // Restore button
            checkoutBtn.innerHTML = originalText;
            checkoutBtn.disabled = false;
        }
    }

    showReceiptModal(result) {
        const modal = new bootstrap.Modal(document.getElementById('receiptModal'));
        
        // Update receipt details
        document.getElementById('receipt-details').innerHTML = `
            <div class="row">
                <div class="col-6"><strong>ID Transaksi:</strong></div>
                <div class="col-6">${result.transaction_id}</div>
            </div>
            <div class="row">
                <div class="col-6"><strong>Total:</strong></div>
                <div class="col-6">${this.formatCurrency(result.total)}</div>
            </div>
            <div class="row">
                <div class="col-6"><strong>Bayar:</strong></div>
                <div class="col-6">${this.formatCurrency(result.payment)}</div>
            </div>
            <div class="row">
                <div class="col-6"><strong>Kembalian:</strong></div>
                <div class="col-6">${this.formatCurrency(result.change)}</div>
            </div>
        `;

        // Update receipt links
        document.getElementById('preview-receipt-btn').href = `/receipt/preview/${result.transaction_id}`;
        document.getElementById('download-receipt-btn').href = `/receipt/pdf/${result.transaction_id}`;

        modal.show();
    }

    clearCart() {
        this.cart = [];
        this.updateCartDisplay();
        document.getElementById('payment-amount').value = '';
        this.showAlert('Keranjang dikosongkan', 'info');
    }

    formatCurrency(amount) {
        return `Rp ${amount.toLocaleString('id-ID')}`;
    }

    updateProductStock() {
        // Update product stock display in real-time after checkout
        this.cart.forEach(cartItem => {
            const productCard = document.querySelector(`[data-product-id="${cartItem.id}"]`);
            if (productCard) {
                const currentStock = parseInt(productCard.dataset.productStock);
                const newStock = currentStock - cartItem.quantity;
                
                // Update stock display
                productCard.dataset.productStock = newStock;
                const stockDisplay = productCard.querySelector('.card-text small');
                if (stockDisplay) {
                    stockDisplay.textContent = `Stok: ${newStock}`;
                }
                
                // Update button and badge based on new stock
                const addButton = productCard.querySelector('.add-to-cart-btn');
                const stockBadge = productCard.querySelector('.low-stock-badge');
                
                if (newStock <= 0) {
                    productCard.classList.add('border-danger');
                    if (addButton) {
                        addButton.innerHTML = '<i class="fas fa-times me-1"></i>Habis';
                        addButton.disabled = true;
                        addButton.className = 'btn btn-secondary btn-sm';
                    }
                    if (stockBadge) {
                        stockBadge.textContent = 'Habis';
                        stockBadge.className = 'badge bg-danger low-stock-badge';
                    }
                } else if (newStock <= 10) {
                    if (stockBadge) {
                        stockBadge.textContent = 'Stok Rendah';
                        stockBadge.className = 'badge bg-warning low-stock-badge';
                    }
                }
            }
        });
    }

    showAlert(message, type) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert at the beginning of main content
        const main = document.querySelector('main');
        main.insertBefore(alertDiv, main.firstChild);

        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Initialize POS system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.pos = new POSSystem();
});
