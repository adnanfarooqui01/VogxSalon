# VOGX Salon - Phase 6 Frontend

## Overview
Phase 6 completes the frontend implementation with a responsive, single-page application using vanilla JavaScript and the Django template system.

## Architecture

### Technology Stack
- **Frontend Framework**: Vanilla JavaScript (no framework)
- **Template Engine**: Django Templates ({% load static %}, template tags)
- **Styling**: Pure CSS3 with CSS custom properties for theming
- **Responsive Design**: Mobile-first approach with breakpoints at 768px and 480px
- **Design System**: Dark theme (#2c3e50) with white background

### Folder Structure
```
VogxSalon/
├── templates/               # Django HTML templates
│   ├── index.html          # Home page / landing page
│   ├── login.html          # Phone + OTP login flow
│   ├── services.html       # Services listing with filters
│   ├── bookings.html       # User's bookings management
│   ├── profile.html        # User profile & payment history
│   └── base.html           # (Optional) Base template for inheritance
├── static/
│   ├── css/
│   │   └── style.css       # Complete responsive design system
│   └── js/
│       └── api.js          # VogxAPI class for backend communication
└── frontend_views.py       # Django views to serve templates
```

## Pages

### 1. **Home Page** (`/`)
- **File**: `templates/index.html`
- **Features**:
  - Hero section with CTA button
  - Services preview (first 3 services)
  - Features highlight section
  - Authentication state detection
  - Shows "Login" button or user menu based on auth

### 2. **Login Page** (`/login`)
- **File**: `templates/login.html`
- **Features**:
  - Phone number input (10 digits)
  - OTP verification step
  - Name input for new users
  - 2-step authentication flow
  - Token storage in localStorage
  - Redirect to home on successful login

### 3. **Services Page** (`/services`)
- **File**: `templates/services.html`
- **Features**:
  - Complete service listing with pagination
  - Category filter dropdown
  - Responsive grid layout (3 columns on desktop)
  - "Book Now" button (requires login)
  - Service details display (price, duration, description)
  - Load More functionality

### 4. **Bookings Page** (`/bookings`)
- **File**: `templates/bookings.html`
- **Features**:
  - User's bookings list
  - Status filter (pending, confirmed, completed, etc.)
  - Booking details card with:
    - Service name
    - Booking date and time
    - Duration and total price
    - Current status and payment status
  - Action buttons (Proceed to Payment, Cancel, View Details)
  - Requires authentication

### 5. **Profile Page** (`/profile`)
- **File**: `templates/profile.html`
- **Features**:
  - User information display
  - Edit name and email
  - Phone number display (read-only)
  - Join date display
  - Payment history table
  - Form validation
  - Update profile functionality
  - Requires authentication

## Design System

### CSS Variables (`:root`)
```css
--primary-color: #2c3e50;        /* Dark blue-gray */
--primary-dark: #34495e;         /* Darker shade for hover */
--background: #ffffff;           /* White background */
--text-dark: #2c3e50;            /* Dark text */
--text-muted: #7f8c8d;           /* Gray text */
--border-color: #ecf0f1;         /* Light border */
--success: #27ae60;              /* Green */
--danger: #e74c3c;               /* Red */
--warning: #f39c12;              /* Orange */
```

### Component Classes
- **Buttons**: `.btn` (primary, secondary, success, danger, full, sm, lg)
- **Cards**: `.card` with `.card-header`, `.card-body`, `.card-footer`
- **Alerts**: `.alert` (alert-success, alert-error, alert-info)
- **Forms**: `.form-group` with proper spacing
- **Modal**: `.modal` with `.modal-content`, `.modal-header`, `.modal-body`
- **Grid**: `.grid` (grid-2, grid-3, grid-4) for responsive layouts
- **Utility**: Margin, padding, text alignment, color classes

### Responsive Breakpoints
- **Desktop**: >= 1024px (3 columns, full nav)
- **Tablet**: >= 768px (2 columns, responsive nav)
- **Mobile**: < 768px (1 column, hamburger nav)

## API Client (api.js)

### VogxAPI Class
Centralized API communication with:
- Token management (localStorage persistence)
- Authentication methods:
  - `phoneLogin(phone)` - Request OTP
  - `verifyOTP(phone, otp, name)` - Verify OTP and get token
  - `getProfile()` - Get user profile
  - `updateProfile(name, email)` - Update profile
  - `logout()` - Invalidate token
- Service methods:
  - `getServices(page, category)` - List services with pagination
  - `getCategories()` - Get all categories
- Booking methods:
  - `createBooking(serviceId, date, time, duration, price, notes)` - Create booking
  - `getBookings(page, status)` - List user bookings
  - `getBookingDetail(id)` - Get single booking
  - `updateBooking(id, status)` - Update booking status
- Payment methods:
  - `createPaymentOrder(bookingId)` - Create Razorpay order
  - `verifyPayment(orderId, paymentId, signature)` - Verify payment
  - `getPaymentHistory(page)` - Get payment history
- Utility functions:
  - `showAlert(message, type)` - Display styled alerts
  - `showLoading()` - Display loading spinner
  - `formatDate(dateString)` - Format date to locale string
  - `formatPrice(amount)` - Format price with rupees symbol

## Usage

### Setting Up the Frontend

1. **Ensure Django is configured**:
   ```bash
   cd VogxSalon
   python manage.py collectstatic --noinput  # For production
   python manage.py runserver 127.0.0.1:8000
   ```

2. **Access pages**:
   - Home: http://127.0.0.1:8000/
   - Login: http://127.0.0.1:8000/login
   - Services: http://127.0.0.1:8000/services
   - Bookings: http://127.0.0.1:8000/bookings
   - Profile: http://127.0.0.1:8000/profile

### Authentication Flow
1. User navigates to `/login`
2. Enters 10-digit phone number
3. Clicks "Get OTP" → OTP sent to phone
4. Enters 6-digit OTP
5. (If new user) Enters name
6. Clicks "Verify & Login"
7. Token stored in localStorage
8. Redirected to home page
9. User can now access protected pages

### Adding a New Page
1. Create `templates/new-page.html` following the pattern of existing pages
2. Import `{% load static %}` at the top
3. Link `style.css` and `api.js`
4. Add route to `frontend_views.py`:
   ```python
   @require_http_methods(["GET"])
   def new_page(request):
       return render(request, 'new-page.html')
   ```
5. Add URL path to `salon_project/urls.py`:
   ```python
   path('new-page', new_page, name='new_page'),
   ```

## Performance Optimizations

1. **Static Files Serving**:
   - CSS and JS files served through Django's static files system
   - WhiteNoise compression for production

2. **API Client**:
   - Token caching in localStorage
   - Single API client instance for all requests
   - Proper error handling with user feedback

3. **Responsive Images**:
   - CSS Grid auto-fit for flexible layouts
   - Mobile-first CSS approach
   - Minimal CSS file size (~10KB minified)

## Testing

### Manual Testing Checklist
- [ ] Home page loads and displays services
- [ ] Navigation links work correctly
- [ ] Login page loads
- [ ] OTP flow works (request OTP → verify)
- [ ] Token stored in localStorage
- [ ] Services page shows all services with filters
- [ ] Bookings page accessible only when logged in
- [ ] Profile page displays user info and payment history
- [ ] Responsive design works on mobile (use Chrome DevTools)
- [ ] Logout clears token and redirects

### Browser Compatibility
- Chrome/Edge >= 90
- Firefox >= 88
- Safari >= 14
- Mobile browsers (iOS Safari, Chrome Mobile)

## Security Considerations

1. **Token Management**:
   - Tokens stored in localStorage (consider httpOnly cookie in production)
   - 401 errors redirect to login
   - Token cleared on logout

2. **API Communication**:
   - All requests include Authorization header
   - CORS properly configured
   - CSRF tokens handled by Django

3. **Form Validation**:
   - Client-side validation before API calls
   - Server validates all inputs
   - Error messages user-friendly

## Future Enhancements

1. **Payment Gateway Integration**:
   - Razorpay JavaScript SDK integration
   - Payment confirmation modal
   - Receipt generation

2. **Advanced Features**:
   - Service search and advanced filters
   - Booking calendar view
   - User reviews and ratings
   - Service recommendations

3. **Performance**:
   - Lazy loading for images
   - Service Worker for offline support
   - Code splitting with dynamic imports

4. **Accessibility**:
   - ARIA labels for screen readers
   - Keyboard navigation
   - High contrast mode support

## Troubleshooting

### Pages Not Loading
- Ensure Django server is running: `python manage.py runserver 127.0.0.1:8000`
- Check browser console for JavaScript errors (F12)
- Verify static files are served: Visit `/static/css/style.css` directly

### API Calls Failing
- Check backend API is running at `/api/` endpoints
- Verify CORS is enabled in Django settings
- Check browser network tab for 401/403 errors
- Ensure token is stored in localStorage

### Styling Issues
- Clear browser cache (Ctrl+Shift+Delete)
- Check CSS file is loaded (Network tab → style.css)
- Verify CSS variables in `:root` section
- Test responsive design at different viewport sizes

---

**Status**: ✓ Phase 6 Complete
**Last Updated**: June 2026
**Team**: VOGX Salon Development
