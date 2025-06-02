// Inventory Management JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Category filter functionality
    const categoryFilters = document.querySelectorAll('input[name="filter-category"]');
    categoryFilters.forEach(filter => {
        filter.addEventListener('change', function() {
            filterProductsByCategory(this.value);
        });
    });

    // Delete stock modal events
    const deleteStockModal = document.getElementById('deleteStockModal');
    if (deleteStockModal) {
        deleteStockModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const productId = button.getAttribute('data-product-id');
            const productName = button.getAttribute('data-product-name');
            const productStock = button.getAttribute('data-product-stock');

            document.getElementById('deleteStockProductName').textContent = productName;
            document.getElementById('deleteStockProductStock').textContent = productStock;
            document.getElementById('deleteStockForm').action = `/inventory/delete-stock/${productId}`;
            document.getElementById('deleteStockQuantity').max = productStock;
            document.getElementById('deleteStockQuantity').value = '';
        });
    }

    // Delete product modal events
    const deleteProductModal = document.getElementById('deleteProductModal');
    if (deleteProductModal) {
        deleteProductModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const productId = button.getAttribute('data-product-id');
            const productName = button.getAttribute('data-product-name');

            document.getElementById('deleteProductName').textContent = productName;
            document.getElementById('deleteProductForm').action = `/inventory/delete/${productId}`;
        });
    }

    // Form validation for add product
    const addProductForm = document.querySelector('#addProductModal form');
    if (addProductForm) {
        addProductForm.addEventListener('submit', function(event) {
            const name = document.getElementById('name').value.trim();
            const price = parseFloat(document.getElementById('price').value);
            const stock = parseInt(document.getElementById('stock').value);
            const category = document.getElementById('category').value;

            if (!name) {
                event.preventDefault();
                showAlert('Nama produk tidak boleh kosong', 'danger');
                return;
            }

            if (price <= 0) {
                event.preventDefault();
                showAlert('Harga harus lebih dari 0', 'danger');
                return;
            }

            if (stock < 0) {
                event.preventDefault();
                showAlert('Stok tidak boleh negatif', 'danger');
                return;
            }

            if (!category) {
                event.preventDefault();
                showAlert('Pilih kategori produk', 'danger');
                return;
            }
        });
    }

    // Form validation for delete stock
    const deleteStockForm = document.getElementById('deleteStockForm');
    if (deleteStockForm) {
        deleteStockForm.addEventListener('submit', function(event) {
            const quantity = parseInt(document.getElementById('deleteStockQuantity').value);
            const maxStock = parseInt(document.getElementById('deleteStockQuantity').max);

            if (!quantity || quantity <= 0) {
                event.preventDefault();
                showAlert('Masukkan jumlah yang valid', 'danger');
                return;
            }

            if (quantity > maxStock) {
                event.preventDefault();
                showAlert('Jumlah tidak boleh lebih dari stok tersedia', 'danger');
                return;
            }
        });
    }
});

function filterProductsByCategory(category) {
    const tableBody = document.getElementById('products-table-body');
    const rows = tableBody.querySelectorAll('tr');

    rows.forEach(row => {
        const rowCategory = row.getAttribute('data-category');
        if (category === 'all' || rowCategory === category) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function showAlert(message, type) {
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

// Auto-format price input
document.addEventListener('DOMContentLoaded', function() {
    const priceInputs = document.querySelectorAll('input[name="price"]');
    priceInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const value = parseFloat(this.value);
            if (!isNaN(value)) {
                this.value = Math.round(value / 100) * 100; // Round to nearest 100
            }
        });
    });
});

// Confirm delete actions
function confirmDelete(message) {
    return confirm(message || 'Apakah Anda yakin ingin menghapus item ini?');
}

// Enhanced form validation with real-time feedback
document.addEventListener('DOMContentLoaded', function() {
    // Real-time validation for product name
    const nameInput = document.getElementById('name');
    if (nameInput) {
        nameInput.addEventListener('input', function() {
            const value = this.value.trim();
            if (value.length < 2) {
                this.setCustomValidity('Nama produk minimal 2 karakter');
            } else {
                this.setCustomValidity('');
            }
        });
    }

    // Real-time validation for price
    const priceInput = document.getElementById('price');
    if (priceInput) {
        priceInput.addEventListener('input', function() {
            const value = parseFloat(this.value);
            if (isNaN(value) || value <= 0) {
                this.setCustomValidity('Harga harus lebih dari 0');
            } else {
                this.setCustomValidity('');
            }
        });
    }

    // Real-time validation for stock
    const stockInput = document.getElementById('stock');
    if (stockInput) {
        stockInput.addEventListener('input', function() {
            const value = parseInt(this.value);
            if (isNaN(value) || value < 0) {
                this.setCustomValidity('Stok tidak boleh negatif');
            } else {
                this.setCustomValidity('');
            }
        });
    }
});
