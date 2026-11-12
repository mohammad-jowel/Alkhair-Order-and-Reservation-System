from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.conf import settings
from accounts.decorators import admin_required
from .models import Reservation
from .forms import ReservationBookingForm


@login_required
def reservation_list(request):
    """
    Customer reservation management: displays booking form and customer's own reservations.
    """
    if request.method == 'POST':
        form = ReservationBookingForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.account = request.user
            reservation.status = 'pending'
            reservation.save()
            messages.success(
                request,
                f'Reservation #{reservation.reservation_id} requested for {reservation.party_size} guest(s) on '
                f'{reservation.reservation_date} at {reservation.reservation_time.strftime("%H:%M")}. '
                'The restaurant will confirm your booking shortly.'
            )
            return redirect('reservations:reservation_list')
    else:
        form = ReservationBookingForm()

    reservations = Reservation.objects.filter(account=request.user).order_by('-reservation_date', '-reservation_time')

    context = {
        'form': form,
        'reservations': reservations,
        'opening_time': getattr(settings, 'OPENING_TIME', '11:00'),
        'closing_time': getattr(settings, 'CLOSING_TIME', '23:30'),
    }
    return render(request, 'reservations/reservation_list.html', context)


@login_required
def cancel_reservation(request, reservation_id):
    """
    Cancel an existing reservation.
    Enforces ownership (returns 404 for other customers' records)
    and business rule: customer can cancel only their own reservation if pending or confirmed.
    """
    if request.method != 'POST':
        return redirect('reservations:reservation_list')

    reservation = get_object_or_404(Reservation, reservation_id=reservation_id)
    if not request.user.is_admin and reservation.account != request.user:
        raise Http404("Reservation not found.")

    if reservation.status in ['pending', 'confirmed']:
        reservation.status = 'cancelled'
        reservation.save()
        messages.success(request, f'Reservation #{reservation.reservation_id} for {reservation.reservation_date} has been cancelled.')
    else:
        messages.error(request, f'Reservation #{reservation.reservation_id} cannot be cancelled as it is already {reservation.get_status_display().lower()}.')

    if request.user.is_admin:
        return redirect('reservations:manage_reservations')
    return redirect('reservations:reservation_list')


@admin_required
def manage_reservations(request):
    """
    Admin reservation dashboard: view all customer bookings and confirm or reject them.
    """
    reservations = Reservation.objects.select_related('account').all().order_by('-reservation_date', '-reservation_time')

    status_filter = request.GET.get('status')
    if status_filter:
        reservations = reservations.filter(status=status_filter)

    if request.method == 'POST':
        reservation_id = request.POST.get('reservation_id')
        action = request.POST.get('action')
        res = get_object_or_404(Reservation, reservation_id=reservation_id)

        if action == 'confirm':
            res.status = 'confirmed'
            res.save()
            messages.success(request, f'Reservation #{res.reservation_id} for {res.account.full_name} is now CONFIRMED.')
        elif action == 'reject':
            res.status = 'rejected'
            res.save()
            messages.warning(request, f'Reservation #{res.reservation_id} for {res.account.full_name} has been REJECTED.')
        return redirect('reservations:manage_reservations')

    context = {
        'reservations': reservations,
        'status_filter': status_filter,
        'status_choices': Reservation.STATUS_CHOICES,
    }
    return render(request, 'reservations/manage_reservations.html', context)
