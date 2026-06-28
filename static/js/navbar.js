/* Navbar and Auth Management */

const api = typeof VogxAPI !== 'undefined' ? new VogxAPI() : null;

// Initialize navbar on page load
document.addEventListener('DOMContentLoaded', function() {
    updateNavbarAuthState();
    updateCartBadge();
    setupGenderToggleIfNeeded();
});

/**
 * Update navbar auth state based on localStorage token
 * Shows either Login button or Profile button
 */
async function updateNavbarAuthState() {
    const token = localStorage.getItem('auth_token');
    const loginBtn = document.getElementById('loginBtn');
    const profileBtn = document.getElementById('profileBtn');
    
    if (token && api) {
        // Token exists - show profile, hide login
        loginBtn.style.display = 'none';
        profileBtn.style.display = 'inline-block';
    } else {
        // No token - show login, hide profile
        loginBtn.style.display = 'inline-block';
        profileBtn.style.display = 'none';
    }
}

/**
 * Open login popup
 */
function openLoginPopup(e) {
    if (e) e.preventDefault();
    const modal = document.getElementById('loginModal');
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    
    // Reset form
    resetLoginForm();
    showLoginStep1();
}

/**
 * Close login popup
 */
function closeLoginPopup(e) {
    if (e && e.target.id !== 'loginModal') return;
    
    const modal = document.getElementById('loginModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    resetLoginForm();
}

/**
 * Reset login form to initial state
 */
function resetLoginForm() {
    document.getElementById('phoneForm').reset();
    document.getElementById('otpForm').reset();
    document.getElementById('phoneError').style.display = 'none';
    document.getElementById('otpError').style.display = 'none';
    document.getElementById('phoneLoading').style.display = 'none';
    document.getElementById('otpLoading').style.display = 'none';
}

/**
 * Show login step 1 (phone entry)
 */
function showLoginStep1() {
    document.getElementById('loginStep1').style.display = 'block';
    document.getElementById('loginStep2').style.display = 'none';
}

/**
 * Show login step 2 (OTP entry)
 */
function showLoginStep2() {
    document.getElementById('loginStep1').style.display = 'none';
    document.getElementById('loginStep2').style.display = 'block';
    document.getElementById('otpInput').focus();
    startResendCountdown();
}

/**
 * Go back from OTP step to phone step
 */
function goBackToPhoneStep() {
    resetLoginForm();
    showLoginStep1();
}

/**
 * Submit phone form - request OTP
 */
async function submitPhoneForm(e) {
    e.preventDefault();
    
    const phone = document.getElementById('phoneInput').value;
    const errorDiv = document.getElementById('phoneError');
    const loadingDiv = document.getElementById('phoneLoading');
    
    if (phone.length !== 10) {
        errorDiv.textContent = 'Please enter a valid 10-digit phone number';
        errorDiv.style.display = 'block';
        return;
    }
    
    errorDiv.style.display = 'none';
    loadingDiv.style.display = 'block';
    
    try {
        // Store phone in sessionStorage for later verification step
        sessionStorage.setItem('login_phone', phone);
        
        const response = await api.request('/auth/send-otp/', 'POST', { phone });
        
        loadingDiv.style.display = 'none';
        showLoginStep2();
    } catch (error) {
        loadingDiv.style.display = 'none';
        if (error.message.includes('limit reached') || error.message.includes('Try again')) {
            errorDiv.textContent = error.message;
        } else if (error.message.includes('wait')) {
            errorDiv.textContent = error.message;
        } else {
            errorDiv.textContent = 'Could not send OTP. Try again.';
        }
        errorDiv.style.display = 'block';
    }
}

/**
 * Submit OTP form - verify OTP and login
 */
async function submitOTPForm(e) {
    e.preventDefault();
    
    const otp = document.getElementById('otpInput').value;
    const name = document.getElementById('nameInput').value || '';
    const phone = sessionStorage.getItem('login_phone');
    const errorDiv = document.getElementById('otpError');
    const loadingDiv = document.getElementById('otpLoading');
    
    if (otp.length !== 6) {
        errorDiv.textContent = 'Please enter a valid 6-digit OTP';
        errorDiv.style.display = 'block';
        return;
    }
    
    errorDiv.style.display = 'none';
    loadingDiv.style.display = 'block';
    
    try {
        const response = await api.request('/auth/verify-otp/', 'POST', {
            phone,
            otp,
            name
        });
        
        // Store token
        if (response.token) {
            localStorage.setItem('auth_token', response.token);
            api.setToken(response.token);
        }
        
        loadingDiv.style.display = 'none';
        closeLoginPopup();
        
        // Update navbar immediately
        updateNavbarAuthState();
        
        // Show success message
        showSuccessMessage('Login successful! 🎉');
        
        // Resume any pending action (handled by calling code)
        if (window.onLoginSuccess) {
            window.onLoginSuccess();
        }
    } catch (error) {
        loadingDiv.style.display = 'none';
        errorDiv.textContent = error.message || 'OTP verification failed. Please try again.';
        errorDiv.style.display = 'block';
    }
}

/**
 * Resend OTP with cooldown
 */
async function resendOTP() {
    const phone = sessionStorage.getItem('login_phone');
    const resendBtn = document.getElementById('resendBtn');
    const errorDiv = document.getElementById('otpError');
    
    if (!phone) {
        errorDiv.textContent = 'Session expired. Please start over.';
        errorDiv.style.display = 'block';
        return;
    }
    
    try {
        await api.request('/auth/send-otp/', 'POST', { phone });
        errorDiv.style.display = 'none';
        startResendCountdown();
    } catch (error) {
        if (error.message.includes('wait')) {
            errorDiv.textContent = error.message;
        } else {
            errorDiv.textContent = 'Could not resend OTP. Try again.';
        }
        errorDiv.style.display = 'block';
    }
}

/**
 * Start 30-second countdown before allowing resend
 */
function startResendCountdown() {
    let seconds = 30;
    const resendBtn = document.getElementById('resendBtn');
    const resendCountdown = document.getElementById('resendCountdown');
    const countdown = document.getElementById('countdown');
    
    resendBtn.style.display = 'none';
    resendCountdown.style.display = 'inline';
    resendBtn.disabled = true;
    
    const interval = setInterval(() => {
        seconds--;
        countdown.textContent = seconds;
        
        if (seconds <= 0) {
            clearInterval(interval);
            resendCountdown.style.display = 'none';
            resendBtn.style.display = 'inline-block';
            resendBtn.disabled = false;
        }
    }, 1000);
}

/**
 * Show temporary success message
 */
function showSuccessMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'success-message';
    messageDiv.textContent = message;
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #4caf50;
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    `;
    document.body.appendChild(messageDiv);
    
    setTimeout(() => {
        messageDiv.remove();
    }, 3000);
}

/**
 * Update cart badge count
 */
function updateCartBadge() {
    const cart = getCart();
    const badge = document.getElementById('cartBadge');
    if (badge) {
        badge.textContent = cart.length;
    }
}

/**
 * Get cart from localStorage
 */
function getCart() {
    const cartJSON = localStorage.getItem('vogx_cart');
    return cartJSON ? JSON.parse(cartJSON) : [];
}

/**
 * Set up gender toggle buttons if on services listing page
 */
function setupGenderToggleIfNeeded() {
    const genderToggle = document.getElementById('genderToggle');
    if (!genderToggle) return;
    
    // Only show on services listing page
    if (window.location.pathname === '/services') {
        genderToggle.style.display = 'flex';
        
        const genderBtns = genderToggle.querySelectorAll('.gender-btn');
        genderBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const gender = this.dataset.gender;
                window.location.href = `/services?gender=${gender}`;
            });
        });
        
        // Set active button based on current query param
        const params = new URLSearchParams(window.location.search);
        const currentGender = params.get('gender') || 'men';
        genderBtns.forEach(btn => {
            if (btn.dataset.gender === currentGender) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }
}

/**
 * Logout user
 */
async function logout() {
    try {
        await api.request('/auth/logout/', 'POST');
    } catch (error) {
        console.log('Logout request failed:', error);
    }
    
    // Clear token regardless
    localStorage.removeItem('auth_token');
    api.clearToken();
    updateNavbarAuthState();
    
    // Redirect to home
    window.location.href = '/';
}

/**
 * Trigger login before action (e.g., "Add to cart" or "Proceed to book")
 */
function loginIfNeeded(callback) {
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
        window.onLoginSuccess = callback;
        openLoginPopup();
    } else {
        callback();
    }
}
