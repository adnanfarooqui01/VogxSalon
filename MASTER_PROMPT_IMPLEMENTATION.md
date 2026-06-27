# VOGX Salon - Master Prompt Implementation Guide

## ✅ BACKEND IMPLEMENTATION COMPLETE

### What Was Missing & Now Fixed

#### **Models**
❌ **Before**: Service model only had `image` field  
✅ **Now**: Separate `preview_image` and `detail_image` fields

❌ **Before**: No gender field (men/women/both distinction)  
✅ **Now**: Gender field on `ServiceCategory` and `Package` models

❌ **Before**: No service type distinction  
✅ **Now**: `service_type` field (home, salon, both) on Service

❌ **Before**: No Package model  
✅ **Now**: `Package` model with ManyToMany services

❌ **Before**: No ServiceStep model  
✅ **Now**: `ServiceStep` model for service process/steps

#### **Admin Panel**
✅ **ServiceCategory Admin**: 
- Gender selection (Men/Women/Both)
- Order field for homepage ordering
- `show_on_home` checkbox to control home page display
- Icon field for category images

✅ **Service Admin**: 
- Preview image (for cards/listings)
- Detail image (for detail page only)
- Service type selection (Home/Salon/Both)
- is_available toggle

✅ **NEW: Package Admin**:
- Add multiple services to a package
- Set package price
- Gender selection
- is_available toggle

✅ **NEW: ServiceStep Admin**:
- Add steps for each service
- Step number, title, description

---

## 📱 ADMIN PANEL WALKTHROUGH

### 1. **Upload Service**
1. Go to: `/admin/services/service/add/`
2. Fill in:
   - **Name**: e.g., "Premium Hair Cut"
   - **Category**: Select Men/Women category (create if needed)
   - **Description**: Service description
   - **Price**: ₹500
   - **Duration**: 60 minutes
   - **Preview Image**: Used in service cards
   - **Detail Image**: Used in service detail page
   - **Service Type**: Home / Salon / Both
   - **Is Available**: Check to enable

### 2. **Create Package**
1. Go to: `/admin/services/package/add/`
2. Fill in:
   - **Name**: e.g., "Complete Grooming Package"
   - **Description**: Package details
   - **Services**: Select multiple services (click services to add)
   - **Package Price**: Bundle price
   - **Gender**: Men / Women / Both
   - **Image**: Package cover image
   - **Is Available**: Check to enable

### 3. **Manage Categories**
1. Go to: `/admin/services/servicecategory/`
2. Click "Add Category":
   - **Name**: Hair, Massage, Spa, Grooming, etc.
   - **Icon**: Category image/icon
   - **Gender**: Men / Women / Both
   - **Order**: 1, 2, 3... (controls display order on home)
   - **Show on Home**: ✓ to display on home page
   - **Is Active**: ✓ to enable

### 4. **Add Service Steps**
1. Go to: `/admin/services/servicestep/add/`
2. For each step:
   - **Service**: Select service
   - **Step Number**: 1, 2, 3...
   - **Title**: Step title
   - **Description**: What happens in this step

---

## 🔌 API ENDPOINTS

### Services by Gender
```
GET /api/services/services/?gender=men&is_available=true
GET /api/services/services/?gender=women&is_available=true
```

### Categories by Gender
```
GET /api/services/categories/?gender=men&show_on_home=true
GET /api/services/categories/?gender=women&show_on_home=true
```

### Packages by Gender
```
GET /api/services/packages/?gender=men&is_available=true
GET /api/services/packages/?gender=women&is_available=true
```

### Service Details with Steps
```
GET /api/services/services/<id>/
Response includes "steps": [ {step_number, title, description} ]
```

---

## 🎨 FRONTEND - TO BE BUILT

### Navbar Design (Required)
- **Logo** (left)
- **Men / Women buttons** (center, pill-style toggle)
  - Active button: darker color (#b3174e)
  - Inactive button: light gray
- **Cart icon** with count badge (right)
- **Profile/Login** button (right)

### Home Page Structure
1. **Hero Banner** (full-width image slider)
2. **Admin-Controlled Categories** (show_on_home=true)
   - Men section: Hair, Massage, Grooming, etc.
   - Women section: Hair, Makeup, Spa, Massage, etc.
   - Each category: horizontal scrollable service cards
3. **Packages Section** (separate)
   - Horizontal scrollable package cards
4. **Customer Reviews** ("What Our Customers Say")
5. **Footer** with social links

### Service Listing Page
- **URL**: `/services/?gender=men` or `/services/?gender=women`
- **Packages First** (horizontal scrollable)
- **Category Pills** (sticky at top)
- **Services by Category** (vertical scrollable)
- **Add to Cart** buttons on each

### Service Detail Page
- Large detail image
- Service name, price, "Add to Cart"
- Service steps (dynamically from admin)
- Reviews section
- Similar services

### Cart Page
- Selected items list
- Booking form:
  - Customer name
  - Phone number
  - Service type (Home/Salon)
  - Address (if home): Pincode, House No, Area, Landmark
  - Date selection (Today, Tomorrow, Day After)
  - Time slot selection
  - Payment method (Cash/Online)
- Price summary with fees

---

## 🎨 COLOR THEME (Updated per Master Prompt)

| Element | Color | Hex |
|---------|-------|-----|
| Primary | Maroon/Rose | #b3174e |
| Primary Dark | Dark Maroon | #8e1240 |
| Primary Light | Light Pink | #e8487a |
| Background | Warm Cream | #faf7f2 |
| Text | Dark | #1a1a1a |
| Text Muted | Gray | #6b6b6b |
| Success | Green | #1f9d52 |
| Danger | Red | #c93a3a |
| Warning | Orange | #b8740a |

---

## 📋 STATUS TRACKING

### ✅ COMPLETED
- Backend models (Services, Categories, Packages, Steps)
- Admin panel fully configured
- API endpoints with gender filtering
- Database migrations applied
- Git committed

### ⏳ IN PROGRESS
- Frontend design system (colors, components)
- Navbar with Men/Women toggle
- Home page layout
- Service listing page

### 📋 TODO
- Service detail page
- Cart system with address fields
- Payment integration
- Profile page
- Login/OTP page
- Responsive design testing
- Production deployment

---

## 🚀 NEXT STEPS

### 1. Frontend - Navbar & Home Page
- Create new navbar with Men/Women pill buttons
- Style using maroon theme (#b3174e)
- Display categories only for selected gender

### 2. Package Management
- Test Package creation in admin
- Verify packages appear in API
- Build package cards in frontend

### 3. Service Listing
- Test gender-filtered service API
- Build category pills (sticky)
- Build service cards by category

### 4. Testing Checklist
- [ ] Can create service in admin
- [ ] Can create package in admin
- [ ] API returns gender-filtered services
- [ ] API returns packages with services
- [ ] Frontend displays Men/Women categories separately
- [ ] Frontend shows packages section
- [ ] Frontend shows services organized by category

---

## 📝 QUICK REFERENCE

**Admin Panel**: http://127.0.0.1:8000/admin/

**Key Admin Sections**:
- `/admin/services/servicecategory/` - Manage categories (gender, order, show_on_home)
- `/admin/services/service/` - Add services with preview/detail images
- `/admin/services/package/` - Create service packages
- `/admin/services/servicestep/` - Add process steps to services

**API Base URL**: http://127.0.0.1:8000/api/

**Key Endpoints**:
- Services by gender: `/api/services/services/?gender=men`
- Categories by gender: `/api/services/categories/?gender=men&show_on_home=true`
- Packages by gender: `/api/services/packages/?gender=men`

---

## 🔧 TROUBLESHOOTING

### Package not showing in admin?
- Ensure `apps.services.admin` has `@admin.register(Package)`
- Restart Django server
- Clear browser cache

### API returning 404 for packages?
- Check migrations applied: `python manage.py migrate`
- Verify Package in installed_apps (services)
- Check router registration in urls.py

### Gender filter not working?
- Verify category has gender field filled
- Test directly: `/api/services/categories/?gender=men`
- Check DRF filtering is enabled

