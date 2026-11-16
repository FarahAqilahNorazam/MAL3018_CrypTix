from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from database.db import (
    create_event, get_all_events, get_event_by_id, 
    update_event, delete_event, get_all_tickets, get_ticket_statistics
)
from utils.auth_utils import admin_required

admin_event_bp = Blueprint('admin_events', __name__, url_prefix='/admin/events')

@admin_event_bp.route('/')
@admin_required
def list_events():
    """
    Admin View Event List:
    - Lists all events with current capacity and management options (edit, delete).
    """
    events = get_all_events()
    stats = get_ticket_statistics()
    return render_template('admin/events_list.html', events=events, stats=stats, user=g.current_user)


@admin_event_bp.route('/create', methods=['GET', 'POST'])
@admin_required
def new_event():
    """
    Admin Create Event:
    - Fields: Event Title, Description, Event Date, Venue, Total Capacity, Ticket Price.
    """
    if request.method == 'POST':
        title = request.form.get('event_title', '').strip()
        description = request.form.get('description', '').strip()
        event_date = request.form.get('event_date', '').strip()
        venue = request.form.get('venue', '').strip()
        total_capacity = request.form.get('total_capacity', '').strip()
        ticket_price = request.form.get('ticket_price', '').strip()

        if not title or not event_date or not venue or not total_capacity or not ticket_price:
            flash('Please fill in all required fields.', 'danger')
            return render_template('admin/event_form.html', action='create', user=g.current_user)

        try:
            total_cap = int(total_capacity)
            price = float(ticket_price)
            if total_cap <= 0 or price <= 0:
                flash('Capacity and ticket price must be positive numbers.', 'danger')
                return render_template('admin/event_form.html', action='create', user=g.current_user)

            create_event(title, description, event_date, venue, total_cap, price)
            flash(f'Concert event "{title}" has been successfully created!', 'success')
            return redirect(url_for('admin_events.list_events'))
        except ValueError:
            flash('Invalid capacity or price format.', 'danger')
            return render_template('admin/event_form.html', action='create', user=g.current_user)

    return render_template('admin/event_form.html', action='create', user=g.current_user)


@admin_event_bp.route('/<int:event_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_event_route(event_id):
    """
    Admin Edit Event:
    - Modify event title, date, venue, capacity, price, description.
    """
    event = get_event_by_id(event_id)
    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('admin_events.list_events'))

    if request.method == 'POST':
        title = request.form.get('event_title', '').strip()
        description = request.form.get('description', '').strip()
        event_date = request.form.get('event_date', '').strip()
        venue = request.form.get('venue', '').strip()
        total_capacity = request.form.get('total_capacity', '').strip()
        ticket_price = request.form.get('ticket_price', '').strip()

        if not title or not event_date or not venue or not total_capacity or not ticket_price:
            flash('Please fill in all required fields.', 'danger')
            return render_template('admin/event_form.html', action='edit', event=event, user=g.current_user)

        try:
            total_cap = int(total_capacity)
            price = float(ticket_price)
            update_event(event_id, title, description, event_date, venue, total_cap, price)
            flash(f'Event "{title}" updated successfully!', 'success')
            return redirect(url_for('admin_events.list_events'))
        except ValueError:
            flash('Invalid capacity or price format.', 'danger')
            return render_template('admin/event_form.html', action='edit', event=event, user=g.current_user)

    return render_template('admin/event_form.html', action='edit', event=event, user=g.current_user)


@admin_event_bp.route('/<int:event_id>/delete', methods=['POST'])
@admin_required
def delete_event_route(event_id):
    """
    Admin Delete Event:
    - Removes event and cascaded tickets.
    """
    event = get_event_by_id(event_id)
    if event:
        delete_event(event_id)
        flash(f'Concert event "{event["event_title"]}" was deleted.', 'info')
    else:
        flash('Event not found.', 'warning')
    return redirect(url_for('admin_events.list_events'))
