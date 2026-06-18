/* API Helper - Communicates with Django Backend */

const API_BASE_URL = 'http://127.0.0.1:8000/api';

class VogxAPI {
    constructor() {
        this.token = localStorage.getItem('auth_token');
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };
        if (this.token) {
            headers['Authorization'] = `Token ${this.token}`;
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
            headers: this.getHeaders(),
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                if (response.status === 401) {
                    this.clearToken();
                    window.location.href = '/index.html';
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
    async getServices(page = 1, categoryId = null) {
        let url = `/services/services/?page=${page}`;
        if (categoryId) {
            url += `&category=${categoryId}`;
        }
        return this.request(url, 'GET');
    }

    async getCategories() {
        return this.request('/services/categories/', 'GET');
    }

    // Bookings Endpoints
    async createBooking(serviceId, bookingDate, bookingTime, durationMinutes, totalPrice, notes = '') {
        return this.request('/bookings/bookings/', 'POST', {
            service: serviceId,
            booking_date: bookingDate,
            booking_time: bookingTime,
            duration_minutes: durationMinutes,
            total_price: totalPrice,
            notes: notes
        });
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

    async updateBooking(bookingId, status, notes = '') {
        return this.request(`/bookings/bookings/${bookingId}/`, 'PATCH', {
            status,
            notes
        });
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

    async getPaymentHistory(page = 1, status = null) {
        let url = `/payments/history/?page=${page}`;
        if (status) {
            url += `&status=${status}`;
        }
        return this.request(url, 'GET');
    }
}

// Create global API instance
const api = new VogxAPI();
