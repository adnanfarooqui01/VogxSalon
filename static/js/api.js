/* API Helper - Communicates with Django Backend */

const API_BASE_URL = 'http://127.0.0.1:8000/api';

class VogxAPI {
    constructor() {
        this.token = localStorage.getItem('auth_token');
    }

    // Get CSRF token from cookie or meta tag
    getCSRFToken() {
        let csrfToken = null;
        
        // Try to get from meta tag
        const csrfMetaTag = document.querySelector('[name=csrftoken]');
        if (csrfMetaTag) {
            csrfToken = csrfMetaTag.getAttribute('content');
        }
        
        // Try to get from cookie
        if (!csrfToken) {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'csrftoken') {
                    csrfToken = value;
                    break;
                }
            }
        }
        
        return csrfToken;
    }

    getHeaders(method = 'GET') {
        const headers = {
            'Content-Type': 'application/json',
        };
        if (this.token) {
            headers['Authorization'] = `Token ${this.token}`;
        }
        
        // Add CSRF token for POST/PUT/PATCH/DELETE requests
        if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method.toUpperCase())) {
            const csrfToken = this.getCSRFToken();
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
            }
        }
        
        return headers;
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('auth_token', token);
    }

    clearToken() {
        this.token = null;
        localStorage.removeItem('auth_token');
    }

    async request(endpoint, method = 'GET', data = null) {
        const url = `${API_BASE_URL}${endpoint}`;
        const options = {
            method,
            headers: this.getHeaders(method),
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                if (response.status === 401) {
                    this.clearToken();
                    window.location.href = '/login';
                }
                const errorData = await response.json();
                throw new Error(errorData.detail || 'API Error');
            }
            return await response.json();
        } catch (error) {
            throw error;
        }
    }

    // Auth Endpoints
    async phoneLogin(phone) {
        return this.request('/auth/phone-login/', 'POST', { phone });
    }

    async verifyOTP(phone, otp, name = '') {
        return this.request('/auth/verify-otp/', 'POST', { phone, otp, name });
    }

    async getProfile() {
        return this.request('/auth/profile/', 'GET');
    }

    async updateProfile(name, email) {
        return this.request('/auth/profile/', 'PUT', { name, email });
    }

    async logout() {
        return this.request('/auth/logout/', 'POST');
    }

    // Services Endpoints
    async getServices(page = 1, categoryId = null, gender = null) {
        let url = `/services/services/?page=${page}&is_available=true`;
        if (categoryId) {
            url += `&category=${categoryId}`;
        }
        if (gender) {
            url += `&gender=${gender}`;
        }
        return this.request(url, 'GET');
    }

    async getServiceDetail(serviceId) {
        return this.request(`/services/services/${serviceId}/`, 'GET');
    }

    async getCategories(gender = null) {
        let url = '/services/categories/?show_on_home=true';
        if (gender) {
            url += `&gender=${gender}`;
        }
        return this.request(url, 'GET');
    }

    // Packages Endpoints
    async getPackages(page = 1, gender = null) {
        let url = `/services/packages/?page=${page}&is_available=true`;
        if (gender) {
            url += `&gender=${gender}`;
        }
        return this.request(url, 'GET');
    }

    async getPackageDetail(packageId) {
        return this.request(`/services/packages/${packageId}/`, 'GET');
    }

    // Bookings Endpoints
    async createBooking(data) {
        return this.request('/bookings/bookings/', 'POST', data);
    }

    async getBookings(page = 1, status = null) {
        let url = `/bookings/bookings/?page=${page}`;
        if (status) {
            url += `&status=${status}`;
        }
        return this.request(url, 'GET');
    }

    async getBookingDetail(bookingId) {
        return this.request(`/bookings/bookings/${bookingId}/`, 'GET');
    }

    async updateBooking(bookingId, data) {
        return this.request(`/bookings/bookings/${bookingId}/`, 'PATCH', data);
    }

    // Payments Endpoints
    async createPaymentOrder(bookingId) {
        return this.request('/payments/create-order/', 'POST', { booking_id: bookingId });
    }

    async verifyPayment(orderId, paymentId, signature) {
        return this.request('/payments/verify-payment/', 'POST', {
            razorpay_order_id: orderId,
            razorpay_payment_id: paymentId,
            razorpay_signature: signature
        });
    }

    async getPaymentHistory(page = 1) {
        let url = `/payments/payments/?page=${page}`;
        return this.request(url, 'GET');
    }

    // Reviews Endpoints
    async getReviews(page = 1) {
        return this.request(`/bookings/reviews/?page=${page}`, 'GET');
    }

    async createReview(bookingId, rating, comment) {
        return this.request('/bookings/reviews/', 'POST', {
            booking: bookingId,
            rating,
            comment
        });
    }
}

// Create global API instance
const api = new VogxAPI();

// Utility Functions
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    document.body.insertBefore(alertDiv, document.body.firstChild);
    setTimeout(() => alertDiv.remove(), 5000);
}

function showLoading(element, show = true) {
    if (show) {
        element.innerHTML = '<div class="spinner"></div>';
    }
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatPrice(price) {
    return `₹${parseFloat(price).toFixed(2)}`;
}

function formatTime(timeString) {
    const [hours, minutes] = timeString.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
}
