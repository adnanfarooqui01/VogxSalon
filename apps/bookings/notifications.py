"""
Admin email notification for booking confirmations.

Design choice: sending is wrapped in try/except and never raises. A failed
email (SMTP down, bad credentials, network blip) must NEVER break the
booking/payment flow — the customer's booking is already confirmed (and
possibly already paid); losing that over an email hiccup would be far
worse than just missing one notification. Failures are logged instead.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


def _get_admin_recipients():
    """
    settings.ADMIN_EMAIL is a single string in base.py, but supports
    comma-separated addresses too (e.g. 'owner@x.com,manager@x.com')
    without needing a settings.py change.
    """
    raw = getattr(settings, 'ADMIN_EMAIL', '') or ''
    emails = [e.strip() for e in raw.split(',') if e.strip()]
    return emails


def send_admin_booking_email(group):
    """
    Emails the salon admin(s) full details of a newly confirmed BookingGroup.

    Args:
        group: a BookingGroup instance with status == 'confirmed'.
    """
    try:
        admin_emails = _get_admin_recipients()
        if not admin_emails:
            logger.warning("ADMIN_EMAIL not configured — skipping booking notification email")
            return

        bookings = list(group.bookings.select_related('service', 'package').all())

        # Split into standalone services vs package-derived services, since
        # package items carry total_price=0 individually (the package price
        # is billed once, on the group, not per included service).
        standalone = [b for b in bookings if b.package_id is None]
        packages = {}
        for b in bookings:
            if b.package_id:
                packages.setdefault(b.package, []).append(b)

        service_lines = []
        for b in standalone:
            service_lines.append(f"  - {b.service.name} ({b.duration_minutes} min) — ₹{b.total_price}")
        for package, items in packages.items():
            service_lines.append(f"  - [Package] {package.name} — ₹{package.package_price}")
            for b in items:
                service_lines.append(f"      • {b.service.name} ({b.duration_minutes} min)")
        service_text = "\n".join(service_lines) if service_lines else "  (no services found)"

        service_html_items = []
        for b in standalone:
            service_html_items.append(f"<li>{b.service.name} ({b.duration_minutes} min) — ₹{b.total_price}</li>")
        for package, items in packages.items():
            included = ", ".join(b.service.name for b in items)
            service_html_items.append(
                f"<li><b>[Package] {package.name}</b> — ₹{package.package_price}"
                f"<br><small>Includes: {included}</small></li>"
            )
        service_html = "".join(service_html_items) if service_html_items else "<li>(no services found)</li>"

        payment = getattr(group, 'payment', None)
        payment_status_line = f"{payment.payment_method} ({payment.status})" if payment else "Not yet created"

        address_line = ", ".join(filter(None, [group.house_number, group.street_area, group.landmark])) or "N/A (in-salon)"

        subject = f"New Booking Confirmed — {group.user.name or group.user.phone} — ₹{group.total_price}"

        text_body = f"""A new booking has been confirmed on VOGX Salon.

CUSTOMER
  Name:  {group.user.name or '(not set)'}
  Phone: {group.user.phone}
  Email: {group.user.email or '(not set)'}

BOOKING
  Order ID: #{group.id}
  Date:  {group.booking_date}
  Time:  {group.booking_time}
  Type:  {group.get_booking_type_display()}
  {"Pincode: " + group.pincode if group.booking_type == 'home' and group.pincode else ""}
  Address: {address_line}
  Notes: {group.notes or '(none)'}

SERVICES
{service_text}

PRICING
  Subtotal:        ₹{group.subtotal}
  Service charge:  ₹{group.service_charge}
  Convenience fee: ₹{group.convenience_fee}
  Total:           ₹{group.total_price}

PAYMENT
  Method/Status: {payment_status_line}
  Paid: {'Yes' if group.is_paid else 'No'}
"""

        html_body = f"""
        <h2>New Booking Confirmed — VOGX Salon</h2>
        <h3>Customer</h3>
        <p>
            <b>Name:</b> {group.user.name or '(not set)'}<br>
            <b>Phone:</b> {group.user.phone}<br>
            <b>Email:</b> {group.user.email or '(not set)'}
        </p>
        <h3>Booking #{group.id}</h3>
        <p>
            <b>Date:</b> {group.booking_date}<br>
            <b>Time:</b> {group.booking_time}<br>
            <b>Type:</b> {group.get_booking_type_display()}<br>
            <b>Address:</b> {address_line}<br>
            <b>Notes:</b> {group.notes or '(none)'}
        </p>
        <h3>Services</h3>
        <ul>{service_html}</ul>
        <h3>Pricing</h3>
        <p>
            Subtotal: ₹{group.subtotal}<br>
            Service charge: ₹{group.service_charge}<br>
            Convenience fee: ₹{group.convenience_fee}<br>
            <b>Total: ₹{group.total_price}</b>
        </p>
        <h3>Payment</h3>
        <p>{payment_status_line} — Paid: {'Yes' if group.is_paid else 'No'}</p>
        """

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=admin_emails,
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)

        logger.info(f"Admin booking notification sent for group_id={group.id}")

    except Exception:
        logger.exception(f"Failed to send admin booking email for group_id={getattr(group, 'id', '?')}")