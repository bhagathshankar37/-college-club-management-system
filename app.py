import os
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from models import db, User, Club, Membership, Event, EventRegistration, Announcement

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'college-club-mgmt-system-secret-key-2026-production'
instance_dir = os.path.join(basedir, 'instance')
os.makedirs(instance_dir, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_dir, 'college_clubs.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


# ===================================================================
# Context Processors & Auth Helpers
# ===================================================================
@app.context_processor
def inject_globals():
    current_user = None
    if 'user_id' in session:
        current_user = db.session.get(User, session['user_id'])
    return {
        'current_user': current_user,
        'current_year': datetime.now().year
    }


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please sign in to access this page.', 'warning')
                return redirect(url_for('login'))
            user = db.session.get(User, session['user_id'])
            if not user or not user.is_active:
                session.clear()
                flash('Your account is inactive or not found.', 'danger')
                return redirect(url_for('login'))
            if user.role not in roles and user.role != 'admin':
                flash('You do not have permission to access this area.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return role_required('admin')(f)


def coordinator_required(f):
    return role_required('coordinator', 'admin')(f)


# ===================================================================
# Authentication Routes
# ===================================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        if user:
            if user.is_admin():
                return redirect(url_for('admin_dashboard'))
            elif user.is_coordinator():
                return redirect(url_for('coordinator_dashboard'))
            return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        login_input = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not login_input or not password:
            flash('Please enter both username/email and password.', 'warning')
            return render_template('auth/login.html')

        user = User.query.filter(
            (User.username == login_input) | (User.email == login_input)
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('This account has been deactivated by an administrator.', 'danger')
                return render_template('auth/login.html')

            session['user_id'] = user.id
            session['username'] = user.username
            session['full_name'] = user.full_name
            session['role'] = user.role

            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)

            if user.is_admin():
                return redirect(url_for('admin_dashboard'))
            elif user.is_coordinator():
                return redirect(url_for('coordinator_dashboard'))
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('auth/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        department = request.form.get('department', 'Computer Science')
        year_of_study = request.form.get('year_of_study', '1st Year')

        if not full_name or not username or not email or not password:
            flash('All required fields must be completed.', 'warning')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match. Please verify.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'warning')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Username is already taken. Please choose another.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email is already registered. Please sign in.', 'warning')
            return render_template('auth/register.html')

        new_user = User(
            full_name=full_name,
            username=username,
            email=email,
            department=department,
            year_of_study=year_of_study,
            role='student',
            is_active=True
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        # Log in automatically
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        session['full_name'] = new_user.full_name
        session['role'] = new_user.role

        flash('Account created successfully! Welcome to CampusClubs.', 'success')
        return redirect(url_for('student_dashboard'))

    return render_template('auth/register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))


# ===================================================================
# Public Routes (Landing, Clubs, Events, Announcements)
# ===================================================================
@app.route('/')
def index():
    stats = {
        'total_clubs': Club.query.filter_by(is_active=True).count(),
        'total_events': Event.query.filter_by(is_published=True).count(),
        'total_students': User.query.filter_by(role='student').count()
    }
    featured_clubs = Club.query.filter_by(is_active=True).limit(6).all()
    upcoming_events = Event.query.filter(
        Event.is_published == True,
        Event.event_date >= datetime.now()
    ).order_by(Event.event_date.asc()).limit(6).all()
    recent_announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()

    return render_template('index.html',
                           stats=stats,
                           featured_clubs=featured_clubs,
                           upcoming_events=upcoming_events,
                           recent_announcements=recent_announcements)


@app.route('/clubs')
def clubs_list():
    clubs = Club.query.filter_by(is_active=True).order_by(Club.name.asc()).all()
    return render_template('clubs/list.html', clubs=clubs)


@app.route('/clubs/<int:club_id>')
def club_detail(club_id):
    club = db.get_or_404(Club, club_id)
    members = Membership.query.filter_by(club_id=club.id, status='active').all()
    upcoming_events = Event.query.filter(
        Event.club_id == club.id,
        Event.is_published == True,
        Event.event_date >= datetime.now()
    ).order_by(Event.event_date.asc()).all()

    is_member = False
    if 'user_id' in session:
        is_member = club.is_user_member(session['user_id'])

    return render_template('clubs/detail.html',
                           club=club,
                           members=members,
                           upcoming_events=upcoming_events,
                           is_member=is_member)


@app.route('/events')
def events_list():
    upcoming_events = Event.query.filter(
        Event.is_published == True,
        Event.event_date >= datetime.now()
    ).order_by(Event.event_date.asc()).all()

    past_events = Event.query.filter(
        Event.is_published == True,
        Event.event_date < datetime.now()
    ).order_by(Event.event_date.desc()).all()

    return render_template('events/list.html',
                           upcoming_events=upcoming_events,
                           past_events=past_events)


@app.route('/events/<int:event_id>')
def event_detail(event_id):
    event = db.get_or_404(Event, event_id)
    is_registered = False
    user_registration = None
    if 'user_id' in session:
        user_registration = EventRegistration.query.filter_by(
            event_id=event.id,
            user_id=session['user_id'],
            status='registered'
        ).first()
        is_registered = user_registration is not None

    return render_template('events/detail.html',
                           event=event,
                           is_registered=is_registered,
                           user_registration=user_registration)


@app.route('/announcements')
def announcements_list():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('announcements.html', announcements=announcements)


# ===================================================================
# Student Actions & Portal Routes
# ===================================================================
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    user = db.session.get(User, session['user_id'])
    joined_clubs = Membership.query.filter_by(user_id=user.id, status='active').all()
    joined_club_ids = [m.club_id for m in joined_clubs]

    registered_events = EventRegistration.query.join(Event).filter(
        EventRegistration.user_id == user.id,
        EventRegistration.status == 'registered',
        Event.event_date >= datetime.now()
    ).order_by(Event.event_date.asc()).all()

    unjoined_clubs = Club.query.filter(
        Club.is_active == True,
        ~Club.id.in_(joined_club_ids) if joined_club_ids else True
    ).limit(4).all()

    recent_announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(6).all()

    return render_template('student/dashboard.html',
                           student=user,
                           joined_clubs=joined_clubs,
                           registered_events=registered_events,
                           unjoined_clubs=unjoined_clubs,
                           recent_announcements=recent_announcements)


@app.route('/student/my-clubs')
@login_required
def student_my_clubs():
    user = db.session.get(User, session['user_id'])
    memberships = Membership.query.filter_by(user_id=user.id, status='active').all()
    return render_template('student/my_clubs.html', memberships=memberships)


@app.route('/student/my-events')
@login_required
def student_my_events():
    user = db.session.get(User, session['user_id'])
    registrations = EventRegistration.query.join(Event).filter(
        EventRegistration.user_id == user.id,
        EventRegistration.status == 'registered'
    ).order_by(Event.event_date.asc()).all()
    return render_template('student/my_events.html', registrations=registrations)


@app.route('/student/profile', methods=['GET', 'POST'])
@login_required
def student_profile():
    user = db.session.get(User, session['user_id'])
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_profile':
            user.full_name = request.form.get('full_name', user.full_name).strip()
            user.avatar_url = request.form.get('avatar_url', '').strip() or None
            user.department = request.form.get('department', user.department)
            user.year_of_study = request.form.get('year_of_study', user.year_of_study)
            db.session.commit()
            session['full_name'] = user.full_name
            flash('Your profile details have been updated.', 'success')
        elif action == 'change_password':
            current_pw = request.form.get('current_password', '')
            new_pw = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_password', '')

            if not user.check_password(current_pw):
                flash('Current password is incorrect.', 'danger')
            elif new_pw != confirm_pw:
                flash('New passwords do not match.', 'danger')
            elif len(new_pw) < 6:
                flash('New password must be at least 6 characters long.', 'warning')
            else:
                user.set_password(new_pw)
                db.session.commit()
                flash('Password changed successfully!', 'success')

        return redirect(url_for('student_profile'))

    return render_template('student/profile.html', user=user)


@app.route('/clubs/<int:club_id>/join', methods=['POST'])
@login_required
def club_join(club_id):
    club = db.get_or_404(Club, club_id)
    user_id = session['user_id']

    existing = Membership.query.filter_by(club_id=club.id, user_id=user_id).first()
    if existing:
        if existing.status == 'active':
            flash(f'You are already an active member of {club.name}.', 'info')
        else:
            existing.status = 'active'
            db.session.commit()
            flash(f'Welcome back! You have rejoined {club.name}.', 'success')
    else:
        new_membership = Membership(
            club_id=club.id,
            user_id=user_id,
            role='Member',
            status='active'
        )
        db.session.add(new_membership)
        db.session.commit()
        flash(f'Congratulations! You have joined {club.name}.', 'success')

    return redirect(request.referrer or url_for('club_detail', club_id=club.id))


@app.route('/clubs/<int:club_id>/leave', methods=['POST'])
@login_required
def club_leave(club_id):
    club = db.get_or_404(Club, club_id)
    user_id = session['user_id']

    membership = Membership.query.filter_by(club_id=club.id, user_id=user_id).first()
    if membership:
        db.session.delete(membership)
        db.session.commit()
        flash(f'You have left {club.name}.', 'info')
    else:
        flash('You are not a member of this club.', 'warning')

    return redirect(request.referrer or url_for('clubs_list'))


@app.route('/events/<int:event_id>/register', methods=['POST'])
@login_required
def event_register(event_id):
    event = db.get_or_404(Event, event_id)
    user_id = session['user_id']

    if event.is_past:
        flash('Registration is closed because this event has already ended.', 'warning')
        return redirect(url_for('event_detail', event_id=event.id))

    if event.is_full:
        flash('Sorry, this event has reached its maximum capacity.', 'danger')
        return redirect(url_for('event_detail', event_id=event.id))

    if event.registration_deadline and event.registration_deadline < datetime.now():
        flash('The registration deadline for this event has passed.', 'warning')
        return redirect(url_for('event_detail', event_id=event.id))

    existing = EventRegistration.query.filter_by(event_id=event.id, user_id=user_id).first()
    if existing:
        if existing.status == 'registered':
            flash('You are already registered for this event.', 'info')
        else:
            existing.status = 'registered'
            db.session.commit()
            flash(f'Your seat for "{event.title}" has been restored! Ticket: {existing.ticket_code}', 'success')
    else:
        registration = EventRegistration(
            event_id=event.id,
            user_id=user_id,
            status='registered'
        )
        db.session.add(registration)
        db.session.commit()
        flash(f'RSVP confirmed for "{event.title}"! Entry Ticket Pass: {registration.ticket_code}', 'success')

    return redirect(url_for('event_detail', event_id=event.id))


@app.route('/events/<int:event_id>/cancel', methods=['POST'])
@login_required
def event_cancel(event_id):
    event = db.get_or_404(Event, event_id)
    user_id = session['user_id']

    registration = EventRegistration.query.filter_by(event_id=event.id, user_id=user_id).first()
    if registration:
        db.session.delete(registration)
        db.session.commit()
        flash(f'Your registration for "{event.title}" has been cancelled.', 'info')
    else:
        flash('No registration found for this event.', 'warning')

    return redirect(request.referrer or url_for('student_my_events'))


# ===================================================================
# Coordinator Routes
# ===================================================================
@app.route('/coordinator/dashboard')
@coordinator_required
def coordinator_dashboard():
    user = db.session.get(User, session['user_id'])
    # Find club coordinated by this user (or first club if admin)
    club = None
    if user.is_coordinator():
        club = Club.query.filter_by(coordinator_id=user.id).first()
    elif user.is_admin():
        club = Club.query.first()

    if not club:
        return render_template('coordinator/dashboard.html', club=None)

    members_count = Membership.query.filter_by(club_id=club.id, status='active').count()
    events = Event.query.filter_by(club_id=club.id).order_by(Event.event_date.desc()).all()
    announcements = Announcement.query.filter_by(club_id=club.id).order_by(Announcement.created_at.desc()).all()
    recent_members = Membership.query.filter_by(club_id=club.id, status='active').order_by(Membership.joined_at.desc()).limit(5).all()
    total_registrations = sum([e.registered_count for e in events])

    return render_template('coordinator/dashboard.html',
                           club=club,
                           members_count=members_count,
                           events=events,
                           announcements=announcements,
                           recent_members=recent_members,
                           total_registrations=total_registrations)


@app.route('/coordinator/club/edit', methods=['GET', 'POST'])
@coordinator_required
def coordinator_manage_club():
    user = db.session.get(User, session['user_id'])
    club = Club.query.filter_by(coordinator_id=user.id).first() if user.is_coordinator() else Club.query.first()
    if not club:
        flash('No club assigned to manage.', 'warning')
        return redirect(url_for('coordinator_dashboard'))

    if request.method == 'POST':
        club.category = request.form.get('category', club.category)
        club.short_description = request.form.get('short_description', club.short_description).strip()
        club.description = request.form.get('description', club.description).strip()
        club.room_or_location = request.form.get('room_or_location', club.room_or_location).strip()
        club.meeting_schedule = request.form.get('meeting_schedule', club.meeting_schedule).strip()
        club.email = request.form.get('email', '').strip() or None
        club.instagram_handle = request.form.get('instagram_handle', '').strip() or None
        club.banner_url = request.form.get('banner_url', '').strip() or None

        db.session.commit()
        flash('Club information updated successfully!', 'success')
        return redirect(url_for('coordinator_dashboard'))

    return render_template('coordinator/manage_club.html', club=club)


@app.route('/coordinator/members')
@coordinator_required
def coordinator_members():
    user = db.session.get(User, session['user_id'])
    club = Club.query.filter_by(coordinator_id=user.id).first() if user.is_coordinator() else Club.query.first()
    if not club:
        flash('No club assigned.', 'warning')
        return redirect(url_for('coordinator_dashboard'))

    members = Membership.query.filter_by(club_id=club.id, status='active').order_by(Membership.joined_at.desc()).all()
    return render_template('coordinator/members.html', club=club, members=members)


@app.route('/coordinator/members/<int:membership_id>/role', methods=['POST'])
@coordinator_required
def coordinator_member_role_update(membership_id):
    membership = db.get_or_404(Membership, membership_id)
    new_role = request.form.get('role', 'Member')
    membership.role = new_role
    db.session.commit()
    flash(f'Role updated for {membership.user.full_name} to {new_role}.', 'success')
    return redirect(url_for('coordinator_members'))


@app.route('/coordinator/members/<int:membership_id>/remove', methods=['POST'])
@coordinator_required
def coordinator_member_remove(membership_id):
    membership = db.get_or_404(Membership, membership_id)
    user_name = membership.user.full_name
    db.session.delete(membership)
    db.session.commit()
    flash(f'{user_name} has been removed from the club.', 'info')
    return redirect(url_for('coordinator_members'))


@app.route('/coordinator/events/new', methods=['GET', 'POST'])
@coordinator_required
def coordinator_event_new():
    user = db.session.get(User, session['user_id'])
    club = Club.query.filter_by(coordinator_id=user.id).first() if user.is_coordinator() else Club.query.first()
    if not club:
        flash('You must have an assigned club to create events.', 'warning')
        return redirect(url_for('coordinator_dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()
        venue_type = request.form.get('venue_type', 'On-Campus')
        event_date_str = request.form.get('event_date')
        deadline_str = request.form.get('registration_deadline')
        max_capacity = int(request.form.get('max_capacity', 100))
        fee = float(request.form.get('fee', 0.0))
        image_url = request.form.get('image_url', '').strip() or None

        if not title or not description or not location or not event_date_str:
            flash('Please fill in all required event details.', 'warning')
            return render_template('coordinator/event_form.html', event=None)

        event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M')
        deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M') if deadline_str else None

        new_event = Event(
            club_id=club.id,
            title=title,
            description=description,
            location=location,
            venue_type=venue_type,
            event_date=event_date,
            registration_deadline=deadline,
            max_capacity=max_capacity,
            fee=fee,
            image_url=image_url,
            is_published=True
        )

        db.session.add(new_event)
        db.session.commit()
        flash(f'Event "{title}" created successfully!', 'success')
        return redirect(url_for('coordinator_dashboard'))

    return render_template('coordinator/event_form.html', event=None)


@app.route('/coordinator/events/<int:event_id>/edit', methods=['GET', 'POST'])
@coordinator_required
def coordinator_event_edit(event_id):
    event = db.get_or_404(Event, event_id)
    user = db.session.get(User, session['user_id'])

    # Verify coordinator owns this club or is admin
    if user.is_coordinator() and event.club.coordinator_id != user.id:
        flash('You are not authorized to edit this event.', 'danger')
        return redirect(url_for('coordinator_dashboard'))

    if request.method == 'POST':
        event.title = request.form.get('title', event.title).strip()
        event.description = request.form.get('description', event.description).strip()
        event.location = request.form.get('location', event.location).strip()
        event.venue_type = request.form.get('venue_type', event.venue_type)
        event_date_str = request.form.get('event_date')
        deadline_str = request.form.get('registration_deadline')
        event.max_capacity = int(request.form.get('max_capacity', event.max_capacity))
        event.fee = float(request.form.get('fee', event.fee))
        event.image_url = request.form.get('image_url', '').strip() or None

        if event_date_str:
            event.event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M')
        if deadline_str:
            event.registration_deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        else:
            event.registration_deadline = None

        db.session.commit()
        flash(f'Event "{event.title}" updated successfully.', 'success')
        return redirect(url_for('coordinator_dashboard'))

    return render_template('coordinator/event_form.html', event=event)


@app.route('/coordinator/events/<int:event_id>/delete', methods=['POST'])
@coordinator_required
def coordinator_event_delete(event_id):
    event = db.get_or_404(Event, event_id)
    user = db.session.get(User, session['user_id'])

    if user.is_coordinator() and event.club.coordinator_id != user.id:
        flash('You are not authorized to delete this event.', 'danger')
        return redirect(url_for('coordinator_dashboard'))

    title = event.title
    db.session.delete(event)
    db.session.commit()
    flash(f'Event "{title}" was deleted.', 'info')
    return redirect(url_for('coordinator_dashboard'))


@app.route('/coordinator/events/<int:event_id>/attendees')
@coordinator_required
def coordinator_event_attendees(event_id):
    event = db.get_or_404(Event, event_id)
    user = db.session.get(User, session['user_id'])

    if user.is_coordinator() and event.club.coordinator_id != user.id:
        flash('You are not authorized to view this attendee list.', 'danger')
        return redirect(url_for('coordinator_dashboard'))

    attendees = EventRegistration.query.filter_by(event_id=event.id).order_by(EventRegistration.registered_at.asc()).all()
    return render_template('coordinator/event_attendees.html', event=event, attendees=attendees)


@app.route('/coordinator/registrations/<int:registration_id>/toggle', methods=['POST'])
@coordinator_required
def coordinator_attendee_status_toggle(registration_id):
    reg = db.get_or_404(EventRegistration, registration_id)
    reg.status = 'attended' if reg.status == 'registered' else 'registered'
    db.session.commit()
    flash(f'Status updated for {reg.user.full_name} to {reg.status}.', 'success')
    return redirect(url_for('coordinator_event_attendees', event_id=reg.event_id))


@app.route('/coordinator/announcements/new', methods=['GET', 'POST'])
@coordinator_required
def coordinator_announcement_new():
    user = db.session.get(User, session['user_id'])
    club = Club.query.filter_by(coordinator_id=user.id).first() if user.is_coordinator() else None

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        priority = request.form.get('priority', 'normal')

        if not title or not content:
            flash('Please provide title and content for announcement.', 'warning')
            return render_template('coordinator/announcement_form.html')

        announcement = Announcement(
            club_id=club.id if club else None,
            author_id=user.id,
            title=title,
            content=content,
            priority=priority
        )

        db.session.add(announcement)
        db.session.commit()
        flash('Announcement broadcasted successfully!', 'success')
        return redirect(url_for('coordinator_dashboard' if user.is_coordinator() else 'announcements_list'))

    return render_template('coordinator/announcement_form.html')


@app.route('/coordinator/announcements/<int:announcement_id>/delete', methods=['POST'])
@coordinator_required
def coordinator_announcement_delete(announcement_id):
    ann = db.get_or_404(Announcement, announcement_id)
    user = db.session.get(User, session['user_id'])

    if user.is_coordinator() and ann.club and ann.club.coordinator_id != user.id:
        flash('You are not authorized to delete this announcement.', 'danger')
        return redirect(url_for('coordinator_dashboard'))

    db.session.delete(ann)
    db.session.commit()
    flash('Announcement deleted.', 'info')
    return redirect(request.referrer or url_for('coordinator_dashboard'))


# ===================================================================
# Admin Control Routes
# ===================================================================
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    stats = {
        'total_users': User.query.count(),
        'total_clubs': Club.query.count(),
        'total_events': Event.query.count(),
        'total_memberships': Membership.query.count(),
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(8).all()
    clubs = Club.query.order_by(Club.name.asc()).all()

    return render_template('admin/dashboard.html',
                           stats=stats,
                           recent_users=recent_users,
                           clubs=clubs)


@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.order_by(User.id.asc()).all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def admin_user_toggle(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == session['user_id']:
        flash('You cannot deactivate your own admin account.', 'danger')
        return redirect(url_for('admin_users'))

    user.is_active = not user.is_active
    db.session.commit()
    status_text = 'activated' if user.is_active else 'deactivated'
    flash(f'User @{user.username} has been {status_text}.', 'success')
    return redirect(request.referrer or url_for('admin_users'))


@app.route('/admin/users/<int:user_id>/role', methods=['POST'])
@admin_required
def admin_user_role(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == session['user_id']:
        flash('You cannot alter your own admin privileges.', 'danger')
        return redirect(url_for('admin_users'))

    new_role = request.form.get('role')
    if new_role in ['student', 'coordinator', 'admin']:
        user.role = new_role
        db.session.commit()
        flash(f'Role for @{user.username} updated to {new_role}.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_user_delete(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == session['user_id']:
        flash('You cannot delete your own admin account.', 'danger')
        return redirect(url_for('admin_users'))

    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'User @{username} has been deleted permanently.', 'info')
    return redirect(url_for('admin_users'))


@app.route('/admin/clubs')
@admin_required
def admin_clubs():
    clubs = Club.query.order_by(Club.name.asc()).all()
    return render_template('admin/clubs.html', clubs=clubs)


@app.route('/admin/clubs/new', methods=['GET', 'POST'])
@admin_required
def admin_club_new():
    coordinators = User.query.filter_by(role='coordinator', is_active=True).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', 'Technical')
        coordinator_id = request.form.get('coordinator_id')
        short_description = request.form.get('short_description', '').strip()
        description = request.form.get('description', '').strip()
        room_or_location = request.form.get('room_or_location', 'Student Center 201').strip()
        meeting_schedule = request.form.get('meeting_schedule', 'Every Wednesday, 4:00 PM').strip()
        email = request.form.get('email', '').strip() or None
        banner_url = request.form.get('banner_url', '').strip() or None

        if not name or not short_description or not description:
            flash('Please complete all required fields.', 'warning')
            return render_template('admin/club_form.html', club=None, coordinators=coordinators)

        slug = name.lower().replace(' ', '-').replace('&', 'and').replace('/', '-')
        coord_id = int(coordinator_id) if coordinator_id and coordinator_id.isdigit() else None

        new_club = Club(
            name=name,
            slug=slug,
            category=category,
            coordinator_id=coord_id,
            short_description=short_description,
            description=description,
            room_or_location=room_or_location,
            meeting_schedule=meeting_schedule,
            email=email,
            banner_url=banner_url,
            is_active=True
        )

        db.session.add(new_club)
        db.session.commit()
        flash(f'Club "{name}" created successfully.', 'success')
        return redirect(url_for('admin_clubs'))

    return render_template('admin/club_form.html', club=None, coordinators=coordinators)


@app.route('/admin/clubs/<int:club_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_club_edit(club_id):
    club = db.get_or_404(Club, club_id)
    coordinators = User.query.filter_by(role='coordinator', is_active=True).all()

    if request.method == 'POST':
        club.name = request.form.get('name', club.name).strip()
        club.category = request.form.get('category', club.category)
        coordinator_id = request.form.get('coordinator_id')
        club.coordinator_id = int(coordinator_id) if coordinator_id and coordinator_id.isdigit() else None
        club.short_description = request.form.get('short_description', club.short_description).strip()
        club.description = request.form.get('description', club.description).strip()
        club.room_or_location = request.form.get('room_or_location', club.room_or_location).strip()
        club.meeting_schedule = request.form.get('meeting_schedule', club.meeting_schedule).strip()
        club.email = request.form.get('email', '').strip() or None
        club.banner_url = request.form.get('banner_url', '').strip() or None

        db.session.commit()
        flash(f'Club "{club.name}" updated.', 'success')
        return redirect(url_for('admin_clubs'))

    return render_template('admin/club_form.html', club=club, coordinators=coordinators)


@app.route('/admin/clubs/<int:club_id>/delete', methods=['POST'])
@admin_required
def admin_club_delete(club_id):
    club = db.get_or_404(Club, club_id)
    name = club.name
    db.session.delete(club)
    db.session.commit()
    flash(f'Club "{name}" and all associated data have been deleted.', 'info')
    return redirect(url_for('admin_clubs'))


# ===================================================================
# Error Handlers
# ===================================================================
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# ===================================================================
# Database Seeding on First Run
# ===================================================================
def seed_database():
    with app.app_context():
        db.create_all()

        if User.query.first() is not None:
            return  # Already seeded

        print("--> Seeding demo database with comprehensive mock data...")

        # 1. Create Admin Account
        admin = User(
            username='admin',
            email='admin@college.edu',
            full_name='Dr. Arthur Pendelton',
            role='admin',
            department='Dean of Student Affairs',
            year_of_study='Faculty Admin',
            avatar_url='https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&auto=format&fit=crop',
            is_active=True
        )
        admin.set_password('Admin@123')
        db.session.add(admin)

        # 2. Create Coordinators
        coords_data = [
            ('coding_lead', 'coding_lead@college.edu', 'David Kim', 'Computer Science', '3rd Year', 'Coord@123', 'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=200&auto=format&fit=crop'),
            ('ai_lead', 'ai_lead@college.edu', 'Sophia Patel', 'Information Technology', '4th Year', 'Coord@123', 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200&auto=format&fit=crop'),
            ('robotics_lead', 'robotics_lead@college.edu', 'Ethan Hunt', 'Mechanical Engineering', '3rd Year', 'Coord@123', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&auto=format&fit=crop'),
            ('cultural_lead', 'cultural_lead@college.edu', 'Aaliyah Ross', 'Design & Media', '2nd Year', 'Coord@123', 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=200&auto=format&fit=crop'),
            ('photo_lead', 'photo_lead@college.edu', 'Leo Martinez', 'Electronics & Communication', '3rd Year', 'Coord@123', 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200&auto=format&fit=crop'),
            ('eclub_lead', 'eclub_lead@college.edu', 'Zack Taylor', 'Business Administration', '4th Year', 'Coord@123', 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&auto=format&fit=crop'),
        ]

        coordinator_objs = []
        for uname, uemail, ufname, udept, uyear, upass, uavatar in coords_data:
            coord = User(
                username=uname,
                email=uemail,
                full_name=ufname,
                department=udept,
                year_of_study=uyear,
                role='coordinator',
                avatar_url=uavatar,
                is_active=True
            )
            coord.set_password(upass)
            db.session.add(coord)
            coordinator_objs.append(coord)

        # 3. Create Students
        students_data = [
            ('alex', 'alex@college.edu', 'Alex Rivera', 'Computer Science', '2nd Year', 'Student@123', 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=200&auto=format&fit=crop'),
            ('priya', 'priya@college.edu', 'Priya Sharma', 'Information Technology', '3rd Year', 'Student@123', 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=200&auto=format&fit=crop'),
            ('marcus', 'marcus@college.edu', 'Marcus Chen', 'Mechanical Engineering', '1st Year', 'Student@123', 'https://images.unsplash.com/photo-1527980965255-d3b416303d12?w=200&auto=format&fit=crop'),
            ('sarah', 'sarah@college.edu', 'Sarah Jenkins', 'Electronics & Communication', '2nd Year', 'Student@123', 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=200&auto=format&fit=crop'),
        ]

        student_objs = []
        for uname, uemail, ufname, udept, uyear, upass, uavatar in students_data:
            student = User(
                username=uname,
                email=uemail,
                full_name=ufname,
                department=udept,
                year_of_study=uyear,
                role='student',
                avatar_url=uavatar,
                is_active=True
            )
            student.set_password(upass)
            db.session.add(student)
            student_objs.append(student)

        db.session.commit()

        # 4. Create 6 Realistic Clubs
        clubs_data = [
            {
                'name': 'Coding Club',
                'slug': 'coding-club',
                'category': 'Technical',
                'coordinator_id': coordinator_objs[0].id,
                'short_description': 'Empowering student developers with competitive programming, web stacks, and open-source hackathons.',
                'description': 'The Coding Club is a vibrant developer collective at the college. We host weekly coding sprints, pair-programming workshops, algorithm mastery sessions, and annual 36-hour hackathons. Whether you are writing your first "Hello World" or architecting scalable distributed systems, our community provides the mentorship and project teams you need.',
                'room_or_location': 'Computer Lab 3, Engineering Block',
                'meeting_schedule': 'Every Wednesday, 4:30 PM',
                'email': 'coding.club@college.edu',
                'instagram_handle': 'campus_coders',
                'banner_url': 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=1000&auto=format&fit=crop'
            },
            {
                'name': 'AI & ML Club',
                'slug': 'ai-ml-club',
                'category': 'Technical',
                'coordinator_id': coordinator_objs[1].id,
                'short_description': 'Exploring the frontier of machine learning, neural networks, computer vision, and generative AI.',
                'description': 'The AI & ML Club explores the cutting edge of artificial intelligence. We explore deep learning architectures, Kaggle competitions, natural language processing, and ethical AI development. Members work on hands-on datasets, conduct research reading groups, and build intelligent applications that solve real-world problems.',
                'room_or_location': 'Data Science Hub, Room 402',
                'meeting_schedule': 'Every Tuesday, 5:00 PM',
                'email': 'aiml.club@college.edu',
                'instagram_handle': 'aiml_campus',
                'banner_url': 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=1000&auto=format&fit=crop'
            },
            {
                'name': 'Robotics Club',
                'slug': 'robotics-club',
                'category': 'Technical',
                'coordinator_id': coordinator_objs[2].id,
                'short_description': 'Building autonomous rovers, drones, IoT hardware, and competing in national robotics arenas.',
                'description': 'The Robotics Club bridges mechanical engineering, embedded programming, and electronics. Members design, 3D-print, solder, and program autonomous vehicles, robotic arms, drone swarms, and combat bots. We regularly represent the college in national inter-university robotics tournaments.',
                'room_or_location': 'Makerspace & Mechatronics Lab',
                'meeting_schedule': 'Every Thursday, 4:00 PM',
                'email': 'robotics@college.edu',
                'instagram_handle': 'campus_robotics',
                'banner_url': 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=1000&auto=format&fit=crop'
            },
            {
                'name': 'Cultural Club',
                'slug': 'cultural-club',
                'category': 'Cultural',
                'coordinator_id': coordinator_objs[3].id,
                'short_description': 'Celebrating music, theatre, dance, and multicultural heritage across vibrant campus fests.',
                'description': 'The Cultural Club is the artistic heartbeat of the campus. From street plays (nukkad natak) and acapella choirs to classical fusion dance and intercultural celebrations, we curate the flagship college festivals and foster student creative expressions on big stages.',
                'room_or_location': 'Amphitheatre & Arts Studio',
                'meeting_schedule': 'Every Friday, 5:30 PM',
                'email': 'cultural.society@college.edu',
                'instagram_handle': 'campus_vibes_culture',
                'banner_url': 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=1000&auto=format&fit=crop'
            },
            {
                'name': 'Photography Club',
                'slug': 'photography-club',
                'category': 'Arts & Media',
                'coordinator_id': coordinator_objs[4].id,
                'short_description': 'Capturing unforgettable campus stories, cinematic photo walks, and digital photo editing.',
                'description': 'The Photography Club is dedicated to the visual arts. We organize golden-hour photo expeditions, portrait lighting workshops, darkroom development, and Lightroom/Photoshop masterclasses. Members also serve as official media photographers for all major college milestones.',
                'room_or_location': 'Media Studio 104',
                'meeting_schedule': 'Every Saturday, 10:00 AM',
                'email': 'shutterbugs@college.edu',
                'instagram_handle': 'campus_lens_club',
                'banner_url': 'https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=1000&auto=format&fit=crop'
            },
            {
                'name': 'Entrepreneurship Club',
                'slug': 'entrepreneurship-club',
                'category': 'Business & Leadership',
                'coordinator_id': coordinator_objs[5].id,
                'short_description': 'Incubating startup ideas, founder pitch sessions, venture capital connects, and business case fests.',
                'description': 'The Entrepreneurship Club (E-Cell) empowers aspiring founders and change-makers. We connect students with venture capitalists, startup mentors, and successful alumni. From idea validation to business model canvas workshops and investor pitch battles, we turn concepts into thriving ventures.',
                'room_or_location': 'Incubation Center, 3rd Floor',
                'meeting_schedule': 'Every Monday, 4:00 PM',
                'email': 'ecell@college.edu',
                'instagram_handle': 'campus_entrepreneurs',
                'banner_url': 'https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=1000&auto=format&fit=crop'
            }
        ]

        club_objs = []
        for cd in clubs_data:
            c = Club(**cd)
            db.session.add(c)
            club_objs.append(c)

        db.session.commit()

        # 5. Seed Memberships
        # Alex is in Coding Club and AI Club
        db.session.add(Membership(user_id=student_objs[0].id, club_id=club_objs[0].id, role='Core Member', status='active', joined_at=datetime.now() - timedelta(days=40)))
        db.session.add(Membership(user_id=student_objs[0].id, club_id=club_objs[1].id, role='Member', status='active', joined_at=datetime.now() - timedelta(days=20)))
        # Priya is in AI Club and Photography Club
        db.session.add(Membership(user_id=student_objs[1].id, club_id=club_objs[1].id, role='Officer', status='active', joined_at=datetime.now() - timedelta(days=50)))
        db.session.add(Membership(user_id=student_objs[1].id, club_id=club_objs[4].id, role='Member', status='active', joined_at=datetime.now() - timedelta(days=15)))
        # Marcus is in Robotics Club and Coding Club
        db.session.add(Membership(user_id=student_objs[2].id, club_id=club_objs[2].id, role='Member', status='active', joined_at=datetime.now() - timedelta(days=10)))
        db.session.add(Membership(user_id=student_objs[2].id, club_id=club_objs[0].id, role='Member', status='active', joined_at=datetime.now() - timedelta(days=5)))
        # Sarah is in Cultural Club and Entrepreneurship Club
        db.session.add(Membership(user_id=student_objs[3].id, club_id=club_objs[3].id, role='Core Member', status='active', joined_at=datetime.now() - timedelta(days=35)))
        db.session.add(Membership(user_id=student_objs[3].id, club_id=club_objs[5].id, role='Member', status='active', joined_at=datetime.now() - timedelta(days=12)))

        db.session.commit()

        # 6. Seed Events (Upcoming & Past)
        now = datetime.now()
        events_data = [
            {
                'club_id': club_objs[0].id,
                'title': 'Full-Stack Web Dev Bootcamp with Flask & React',
                'description': 'Join us for a weekend hands-on sprint where you will build and deploy a full-stack web application from scratch. We cover database schemas, REST APIs, session management, and responsive front-end design.',
                'location': 'CS Lab 3, Engineering Block',
                'venue_type': 'Lab',
                'event_date': now + timedelta(days=5, hours=4),
                'registration_deadline': now + timedelta(days=4),
                'max_capacity': 60,
                'fee': 0.0,
                'image_url': 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=1000&auto=format&fit=crop'
            },
            {
                'club_id': club_objs[1].id,
                'title': 'AI Summit 2026: Generative Models & LLMs',
                'description': 'A full-day tech seminar featuring guest research engineers discussing Transformer architectures, open-weight language models, and practical fine-tuning techniques.',
                'location': 'Main University Auditorium',
                'venue_type': 'Auditorium',
                'event_date': now + timedelta(days=9, hours=2),
                'registration_deadline': now + timedelta(days=8),
                'max_capacity': 150,
                'fee': 0.0,
                'image_url': 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=1000&auto=format&fit=crop'
            },
            {
                'club_id': club_objs[2].id,
                'title': 'RoboWars 2026: Autonomous Rover Challenge',
                'description': 'Witness thrilling head-to-head battles between student-engineered autonomous obstacle-navigating rovers. Cash prizes and internship vouchers for top 3 teams.',
                'location': 'Student Activity Center Arena',
                'venue_type': 'On-Campus',
                'event_date': now + timedelta(days=14, hours=6),
                'registration_deadline': now + timedelta(days=12),
                'max_capacity': 200,
                'fee': 5.0,
                'image_url': 'https://images.unsplash.com/photo-1563770660941-20978e870e26?w=1000&auto=format&fit=crop'
            },
            {
                'club_id': club_objs[3].id,
                'title': 'Annual Inter-College Cultural Fest: Resonance',
                'description': 'The biggest entertainment extravaganza of the semester! Live musical bands, fashion show, street theatre battles, dance crew showdowns, and food trucks.',
                'location': 'Central Campus Grounds',
                'venue_type': 'On-Campus',
                'event_date': now + timedelta(days=21, hours=8),
                'registration_deadline': now + timedelta(days=20),
                'max_capacity': 500,
                'fee': 0.0,
                'image_url': 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=1000&auto=format&fit=crop'
            },
            {
                'club_id': club_objs[4].id,
                'title': 'Campus Golden Hour Photo Walk & Portrait Masterclass',
                'description': 'Bring your DSLR or smartphone and learn framing, natural lighting, bokeh, and shutter speed control with senior campus photographers.',
                'location': 'College Botanical Garden Gate',
                'venue_type': 'On-Campus',
                'event_date': now + timedelta(days=7, hours=10),
                'registration_deadline': now + timedelta(days=6),
                'max_capacity': 30,
                'fee': 0.0,
                'image_url': 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=1000&auto=format&fit=crop'
            },
            {
                'club_id': club_objs[5].id,
                'title': 'Pitch It! Shark Tank College Edition',
                'description': 'Present your 3-minute startup elevator pitch to angel investors and receive direct feedback, seed grant grants, and incubation workspace access.',
                'location': 'Management Conference Hall A',
                'venue_type': 'Auditorium',
                'event_date': now + timedelta(days=18, hours=3),
                'registration_deadline': now + timedelta(days=16),
                'max_capacity': 80,
                'fee': 0.0,
                'image_url': 'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=1000&auto=format&fit=crop'
            },
            {
                'club_id': club_objs[0].id,
                'title': 'Introduction to Git, GitHub & Open-Source',
                'description': 'Past beginner workshop covering branch strategies, pull requests, and preparing for Hacktoberfest.',
                'location': 'Seminar Hall 2',
                'venue_type': 'On-Campus',
                'event_date': now - timedelta(days=12),
                'registration_deadline': now - timedelta(days=13),
                'max_capacity': 80,
                'fee': 0.0,
                'image_url': 'https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=1000&auto=format&fit=crop'
            },
            {
                'club_id': club_objs[1].id,
                'title': 'Intro to Computer Vision with OpenCV',
                'description': 'Past workshop covering edge detection, face tracking, and object classification.',
                'location': 'Data Science Lab 1',
                'venue_type': 'Lab',
                'event_date': now - timedelta(days=25),
                'registration_deadline': now - timedelta(days=26),
                'max_capacity': 50,
                'fee': 0.0,
                'image_url': 'https://images.unsplash.com/photo-1507146426996-ef05306b995a?w=1000&auto=format&fit=crop'
            }
        ]

        event_objs = []
        for ed in events_data:
            ev = Event(**ed)
            db.session.add(ev)
            event_objs.append(ev)

        db.session.commit()

        # 7. Seed Event Registrations
        db.session.add(EventRegistration(event_id=event_objs[0].id, user_id=student_objs[0].id, ticket_code='TKT-COD-01', status='registered'))
        db.session.add(EventRegistration(event_id=event_objs[0].id, user_id=student_objs[1].id, ticket_code='TKT-COD-02', status='registered'))
        db.session.add(EventRegistration(event_id=event_objs[1].id, user_id=student_objs[0].id, ticket_code='TKT-AIM-01', status='registered'))
        db.session.add(EventRegistration(event_id=event_objs[1].id, user_id=student_objs[1].id, ticket_code='TKT-AIM-02', status='registered'))
        db.session.add(EventRegistration(event_id=event_objs[2].id, user_id=student_objs[2].id, ticket_code='TKT-ROB-01', status='registered'))
        db.session.add(EventRegistration(event_id=event_objs[3].id, user_id=student_objs[3].id, ticket_code='TKT-CUL-01', status='registered'))
        db.session.add(EventRegistration(event_id=event_objs[4].id, user_id=student_objs[1].id, ticket_code='TKT-PHT-01', status='registered'))

        # 8. Seed Announcements
        announcements_data = [
            {
                'club_id': None,
                'author_id': admin.id,
                'title': 'Welcome to the New Academic Semester & Club Registration Drive',
                'content': 'All students are encouraged to explore student clubs and register for upcoming orientation sessions. The club directory is now live for open enrollments!',
                'priority': 'important'
            },
            {
                'club_id': club_objs[0].id,
                'author_id': coordinator_objs[0].id,
                'title': 'Coding Club Core Committee Recruitment 2026',
                'content': 'We are hiring Web Leads, Competitive Programming Mentors, and Event Coordinators. Interested candidates should attend the interview session this Friday at 4:30 PM in Lab 3.',
                'priority': 'urgent'
            },
            {
                'club_id': club_objs[1].id,
                'author_id': coordinator_objs[1].id,
                'title': 'Kaggle Competition Teams Formation Meeting',
                'content': 'Forming collegiate teams for the upcoming Kaggle LLM Challenge. Bring your laptops and past ML project portfolios.',
                'priority': 'normal'
            },
            {
                'club_id': club_objs[2].id,
                'author_id': coordinator_objs[2].id,
                'title': 'Components & Microcontroller Kits Distribution',
                'content': 'Registered members for the Rover Challenge can collect their Arduino & ESP32 starter kits from the Mechatronics lab between 3 PM and 5 PM.',
                'priority': 'important'
            },
            {
                'club_id': club_objs[3].id,
                'author_id': coordinator_objs[3].id,
                'title': 'Auditions for Annual Musical Fest Band & Dance Troupe',
                'content': 'Open auditions for vocals, lead guitar, drums, and choreography will take place in the Amphitheatre this Saturday.',
                'priority': 'urgent'
            },
            {
                'club_id': club_objs[5].id,
                'author_id': coordinator_objs[5].id,
                'title': '$10,000 Seed Grant Applications Open for Student Founders',
                'content': 'Submit your pitch decks for the annual venture incubation grant by the end of this month. Guidelines available on the E-Cell portal.',
                'priority': 'important'
            }
        ]

        for ad in announcements_data:
            ann = Announcement(**ad)
            db.session.add(ann)

        db.session.commit()
        print("--> Database seeded successfully with demo users, clubs, events, registrations & bulletins!")


# Trigger initial DB initialization and seeding
seed_database()


if __name__ == '__main__':
    # Start local Flask development server
    app.run(host='127.0.0.1', port=5000, debug=True)
