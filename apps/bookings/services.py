from django.db import transaction

from apps.core.models import ServiceablePincode
from apps.services.models import Service, Package
from .models import Booking, BookingGroup
from .notifications import send_admin_booking_email


def compute_booking_totals(service_ids, package_ids, booking_type, pincode):
    services = list(Service.objects.filter(id__in=service_ids))
    if len(services) != len(service_ids):
        raise ValueError('One or more services not found.')

    packages = list(Package.objects.prefetch_related('services').filter(id__in=package_ids))
    if len(packages) != len(package_ids):
        raise ValueError('One or more packages not found.')

    subtotal = sum(s.price for s in services) + sum(p.package_price for p in packages)
    service_charge = 0
    if booking_type == 'home':
        serviceable = ServiceablePincode.objects.filter(pincode=pincode, is_active=True).first()
        service_charge = serviceable.delivery_charge if serviceable else 0
    convenience_fee = 20
    total_price = subtotal + service_charge + convenience_fee
    return services, packages, subtotal, service_charge, convenience_fee, total_price


@transaction.atomic
def create_booking_group(user, data, status='confirmed'):
    service_ids = data.get('service_ids', []) or []
    package_ids = data.get('package_ids', []) or []
    services, packages, subtotal, service_charge, convenience_fee, total_price = compute_booking_totals(
        service_ids, package_ids, data['booking_type'], data.get('pincode')
    )

    group = BookingGroup.objects.create(
        user=user,
        booking_date=data['booking_date'],
        booking_time=data['booking_time'],
        booking_type=data['booking_type'],
        pincode=data.get('pincode'),
        house_number=data.get('house_number'),
        street_area=data.get('street_area'),
        landmark=data.get('landmark'),
        notes=data.get('notes', ''),
        subtotal=subtotal,
        service_charge=service_charge,
        convenience_fee=convenience_fee,
        total_price=total_price,
        status=status,
    )

    for service in services:
        Booking.objects.create(
            group=group,
            user=user,
            service=service,
            booking_date=data['booking_date'],
            booking_time=data['booking_time'],
            duration_minutes=service.duration_minutes,
            total_price=service.price,
            booking_type=data['booking_type'],
            pincode=data.get('pincode'),
            house_number=data.get('house_number'),
            street_area=data.get('street_area'),
            landmark=data.get('landmark'),
            notes=data.get('notes', ''),
            status=status,
        )

    for package in packages:
        for service in package.services.all():
            Booking.objects.create(
                group=group,
                user=user,
                service=service,
                package=package,
                booking_date=data['booking_date'],
                booking_time=data['booking_time'],
                duration_minutes=service.duration_minutes,
                total_price=0,
                booking_type=data['booking_type'],
                pincode=data.get('pincode'),
                house_number=data.get('house_number'),
                street_area=data.get('street_area'),
                landmark=data.get('landmark'),
                notes=data.get('notes', ''),
                status=status,
            )

    if status == 'confirmed':
        # This single call point covers EVERY way a BookingGroup can be
        # confirmed in this project:
        #   - BookingGroupCreateSerializer.create() (cash / pay-later checkout)
        #   - payments/views.py _finalize_group_payment() (online payment,
        #     both the browser callback AND the webhook safety-net)
        # send_admin_booking_email() never raises — a failed email can't
        # roll back this transaction or block the booking itself.
        send_admin_booking_email(group)

    return group