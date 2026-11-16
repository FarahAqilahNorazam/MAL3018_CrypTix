from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from database.db import (
    get_all_events, get_event_by_id, purchase_tickets, 
    get_tickets_by_user_id, get_user_ticket_count_for_event
)
from utils.auth_utils import login_required

event_bp = Blueprint('events', __name__)

@event_bp.route('/events')
@login_required
def browse_events():
    """
    Browse Events Page:
    - Lists all available concert events in a responsive card grid.
    - Mobile-friendly layout with date, venue, price, and remaining capacity.
    """
    events = get_all_events()
    return render_template('events/browse.html', events=events, user=g.current_user)


@event_bp.route('/events/<int:event_id>')
@login_required
def event_details(event_id):
    """
    Event Details Page:
    - Event information, venue, date and time, ticket price, and available capacity.
    - Checks user's existing ticket holdings to enforce the 4-ticket anti-hoarding rule.
    """
    event = get_event_by_id(event_id)
    if not event:
        flash('Concert event not found.', 'danger')
        return redirect(url_for('events.browse_events'))

    user_id = g.current_user['user_id']
    user_ticket_count = get_user_ticket_count_for_event(user_id, event_id)
    remaining_allowed = max(0, 4 - user_ticket_count)

    return render_template(
        'events/details.html',
        event=event,
        user=g.current_user,
        user_ticket_count=user_ticket_count,
        remaining_allowed=remaining_allowed
    )


@event_bp.route('/events/<int:event_id>/purchase', methods=['POST'])
@login_required
def purchase_ticket(event_id):
    """
    Purchase Ticket Route (Simulated Checkout):
    - Enforces Rule: Maximum 4 tickets per user per event.
    - Decrements available event capacity.
    - Automatically assigns sequential seat numbers.
    """
    user_id = g.current_user['user_id']
    try:
        quantity = int(request.form.get('quantity', 1))
    except ValueError:
        flash('Invalid ticket quantity selected.', 'danger')
        return redirect(url_for('events.event_details', event_id=event_id))

    if quantity < 1 or quantity > 4:
        flash('You may only purchase between 1 and 4 tickets per transaction.', 'danger')
        return redirect(url_for('events.event_details', event_id=event_id))

    success, result = purchase_tickets(event_id, user_id, quantity)

    if success:
        seats_str = ", ".join([t['seat_number'] for t in result])
        flash(f'Payment Simulated Successfully! You purchased {quantity} ticket(s). Assigned Seats: {seats_str}', 'success')
        return redirect(url_for('events.my_tickets'))
    else:
        flash(result, 'danger')
        return redirect(url_for('events.event_details', event_id=event_id))


@event_bp.route('/my-tickets')
@login_required
def my_tickets():
    """
    My Tickets Page:
    - Displays all tickets purchased by the logged-in customer.
    - Shows event title, venue, event date, seat number, and status ('SOLD').
    """
    tickets = get_tickets_by_user_id(g.current_user['user_id'])
    return render_template('events/my_tickets.html', tickets=tickets, user=g.current_user)
