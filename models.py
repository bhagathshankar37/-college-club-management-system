from datetime import datetime
import uuid
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student', 'coordinator', 'admin'
    department = db.Column(db.String(100), default='Computer Science')
    year_of_study = db.Column(db.String(20), default='1st Year')
    avatar_url = db.Column(db.String(300), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    # Relationships
    coordinated_clubs = db.relationship('Club', back_populates='coordinator', lazy=True)
    memberships = db.relationship('Membership', back_populates='user', cascade='all, delete-orphan', lazy=True)
    event_registrations = db.relationship('EventRegistration', back_populates='user', cascade='all, delete-orphan', lazy=True)
    announcements = db.relationship('Announcement', back_populates='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def is_coordinator(self):
        return self.role == 'coordinator'

    def is_student(self):
        return self.role == 'student'

    def get_avatar(self):
        if self.avatar_url:
            return self.avatar_url
        initials = ''.join([part[0] for part in self.full_name.split()[:2]]).upper() if self.full_name else 'U'
        return f"https://ui-avatars.com/api/?name={initials}&background=4f46e5&color=fff&size=128&bold=true"

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Club(db.Model):
    __tablename__ = 'clubs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(140), unique=True, nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False)  # 'Technical', 'Cultural', 'Arts & Media', 'Sports & Fitness', 'Business & Leadership'
    short_description = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(300), nullable=True)
    banner_url = db.Column(db.String(300), nullable=True)
    coordinator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    room_or_location = db.Column(db.String(100), default='Student Center 201')
    email = db.Column(db.String(120), nullable=True)
    instagram_handle = db.Column(db.String(80), nullable=True)
    meeting_schedule = db.Column(db.String(120), default='Every Wednesday, 4:00 PM')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    # Relationships
    coordinator = db.relationship('User', back_populates='coordinated_clubs')
    memberships = db.relationship('Membership', back_populates='club', cascade='all, delete-orphan', lazy=True)
    events = db.relationship('Event', back_populates='club', cascade='all, delete-orphan', lazy=True, order_by='Event.event_date.asc()')
    announcements = db.relationship('Announcement', back_populates='club', cascade='all, delete-orphan', lazy=True, order_by='Announcement.created_at.desc()')

    @property
    def active_members_count(self):
        return Membership.query.filter_by(club_id=self.id, status='active').count()

    @property
    def upcoming_events_count(self):
        return Event.query.filter(
            Event.club_id == self.id,
            Event.is_published == True,
            Event.event_date >= datetime.now()
        ).count()

    def is_user_member(self, user_id):
        if not user_id:
            return False
        return Membership.query.filter_by(club_id=self.id, user_id=user_id, status='active').first() is not None

    def __repr__(self):
        return f'<Club {self.name}>'


class Membership(db.Model):
    __tablename__ = 'memberships'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=False)
    role = db.Column(db.String(50), default='Member', nullable=False)  # 'Member', 'Core Member', 'Officer', 'Lead'
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active', 'inactive'
    joined_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'club_id', name='uq_user_club_membership'),
    )

    # Relationships
    user = db.relationship('User', back_populates='memberships')
    club = db.relationship('Club', back_populates='memberships')

    def __repr__(self):
        return f'<Membership User {self.user_id} - Club {self.club_id}>'


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(150), nullable=False)
    venue_type = db.Column(db.String(50), default='On-Campus', nullable=False)  # 'On-Campus', 'Auditorium', 'Lab', 'Online'
    event_date = db.Column(db.DateTime, nullable=False, index=True)
    end_date = db.Column(db.DateTime, nullable=True)
    registration_deadline = db.Column(db.DateTime, nullable=True)
    max_capacity = db.Column(db.Integer, default=100, nullable=False)
    fee = db.Column(db.Float, default=0.0, nullable=False)
    image_url = db.Column(db.String(300), nullable=True)
    is_published = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    # Relationships
    club = db.relationship('Club', back_populates='events')
    registrations = db.relationship('EventRegistration', back_populates='event', cascade='all, delete-orphan', lazy=True)

    @property
    def registered_count(self):
        return EventRegistration.query.filter_by(event_id=self.id, status='registered').count()

    @property
    def available_seats(self):
        return max(0, self.max_capacity - self.registered_count)

    @property
    def is_full(self):
        return self.registered_count >= self.max_capacity

    @property
    def is_past(self):
        return self.event_date < datetime.now()

    @property
    def is_registration_closed(self):
        if self.is_past:
            return True
        if self.is_full:
            return True
        if self.registration_deadline and self.registration_deadline < datetime.now():
            return True
        return False

    def is_user_registered(self, user_id):
        if not user_id:
            return False
        return EventRegistration.query.filter_by(event_id=self.id, user_id=user_id, status='registered').first() is not None

    def __repr__(self):
        return f'<Event {self.title}>'


class EventRegistration(db.Model):
    __tablename__ = 'event_registrations'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    status = db.Column(db.String(20), default='registered', nullable=False)  # 'registered', 'attended', 'cancelled'
    ticket_code = db.Column(db.String(36), default=lambda: str(uuid.uuid4())[:8].upper(), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('event_id', 'user_id', name='uq_event_user_registration'),
    )

    # Relationships
    event = db.relationship('Event', back_populates='registrations')
    user = db.relationship('User', back_populates='event_registrations')

    def __repr__(self):
        return f'<Registration Event {self.event_id} - User {self.user_id}>'


class Announcement(db.Model):
    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=True)  # None = Campus-wide
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='normal', nullable=False)  # 'normal', 'important', 'urgent'
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    # Relationships
    club = db.relationship('Club', back_populates='announcements')
    author = db.relationship('User', back_populates='announcements')

    def __repr__(self):
        return f'<Announcement {self.title}>'
