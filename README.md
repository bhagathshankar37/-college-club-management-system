# 🎓 College Club Management System

A modern, responsive, full-stack web application designed for collegiate student life management. Students can discover organizations, register for hackathons and workshops, and access campus bulletins. Club coordinators can manage memberships, events, and announcements. Platform administrators possess complete system oversight and role control.

---

## ✨ Features Overview

### 🔐 Authentication & Role-Based Access Control (RBAC)
* **Secure Registration & Login**: Password hashing powered by Werkzeug security utilities.
* **Session-Based Authentication**: Secure server-side session management.
* **Role-Based Permissions**: Strict access segregation across **Student**, **Club Coordinator**, and **Admin** roles.
* **1-Click Demo Login**: Pre-seeded quick login shortcuts on the login screen for rapid testing.

### 🎒 Student Features
* **Personalized Dashboard**: Real-time overview of joined clubs, registered events, entry ticket codes, and campus notices.
* **Club Directory & Exploration**: Filter clubs by category (Technical, Cultural, Arts & Media, Sports, Business) and search in real time.
* **1-Click Club Membership**: Join and leave clubs seamlessly.
* **Event RSVP & Digital Passes**: Register for workshops and competitions, generating unique ticket pass codes (e.g. `PASS #TKT-COD-01`).
* **Profile Management**: Update department, year of study, display avatar, and change password securely.

### 👔 Club Coordinator Features
* **Coordinator Workspace**: Dedicated dashboard displaying active member counts, event rosters, RSVP statistics, and bulletins.
* **Event Lifecycle Management**: Create, edit, publish, and delete events with date/time pickers, seat capacity limits, and venue formats (Lab, Auditorium, Online).
* **Attendee Tracking**: View full student attendee lists and toggle check-in attendance status.
* **Club Customization**: Edit club descriptions, locations, meeting schedules, contact emails, and banner images.
* **Broadcast Announcements**: Publish priority-tagged announcements (Normal, Important, Urgent) to club members.
* **Member Roster Management**: Promote members to Core Member, Officer, or Vice President roles.

### 🛡️ Administrator Features
* **Executive Dashboard**: System-wide statistics (total users, total clubs, total events, total memberships).
* **User Management**: View all platform users, promote/demote user roles, and activate/deactivate accounts.
* **Club Management**: Register new clubs, assign designated student coordinators, and manage organizations.

---

## 🛠️ Technology Stack

* **Backend**: Python 3.10+ / Flask 3.x
* **Database ORM**: SQLite with Flask-SQLAlchemy 3.x
* **Authentication**: Flask Sessions & Werkzeug Password Security
* **Frontend**: HTML5, CSS3, Vanilla JavaScript (ES6+)
* **UI Framework**: Bootstrap 5.3 & Bootstrap Icons CDN
* **Typography**: Google Fonts (*Outfit* & *Inter*)

---

## 📂 Project Structure

```
-college-club-management-system/
├── app.py                     # Main application factory, routes, RBAC decorators, auto-seeder
├── models.py                  # SQLAlchemy models (User, Club, Membership, Event, EventRegistration, Announcement)
├── test_app.py                # Automated integration test suite
├── requirements.txt           # Python dependencies
├── README.md                  # Comprehensive documentation
├── instance/
│   └── college_clubs.db       # SQLite database (auto-generated)
├── static/
│   ├── css/
│   │   └── style.css          # Custom collegiate design system, gradients, cards, and animations
│   └── js/
│       └── main.js            # Live search filters, auto-dismissing alerts, and demo login helpers
└── templates/
    ├── base.html              # Master layout with responsive navbar, toasts, and footer
    ├── index.html             # Landing page with hero stats, featured clubs, and spotlight events
    ├── 404.html               # Custom 404 error page
    ├── 500.html               # Custom 500 error page
    ├── announcements.html     # Campus-wide bulletin board
    ├── auth/
    │   ├── login.html         # Sign in with 1-click test fill chips
    │   └── register.html      # Student registration form
    ├── student/
    │   ├── dashboard.html     # Student hub & widgets
    │   ├── my_clubs.html      # Joined clubs management
    │   ├── my_events.html     # Registered event tickets & cancellations
    │   └── profile.html       # Profile settings & password change
    ├── coordinator/
    │   ├── dashboard.html     # Coordinator hub & metrics
    │   ├── manage_club.html   # Club information editor
    │   ├── members.html       # Enrolled member roster
    │   ├── event_form.html    # Event creation & editing
    │   ├── event_attendees.html # Attendee roster & check-in
    │   └── announcement_form.html # Announcement composer
    ├── admin/
    │   ├── dashboard.html     # System administration panel
    │   ├── users.html         # User permission & status control
    │   ├── clubs.html         # Organization directory
    │   └── club_form.html     # Club registration & coordinator assignment
    ├── clubs/
    │   ├── list.html          # Searchable club catalog
    │   └── detail.html        # Detailed club hub with tabs
    └── events/
        ├── list.html          # Upcoming and past events calendar
        └── detail.html        # Event details & RSVP card
```

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.10 or higher installed on your system.

### 2. Setup Virtual Environment & Install Dependencies

```bash
# Clone the repository and navigate to the directory
cd -college-club-management-system

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS / Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python app.py
```

The application will automatically:
1. Initialize the SQLite database at `instance/college_clubs.db`.
2. Seed initial demo users, 6 clubs, 8+ events, announcements, and memberships.
3. Start the Flask local development server at **`http://127.0.0.1:5000`**.

---

## 🔑 Demo Login Credentials

You can log in manually using these credentials or click any **One-Click Demo Test** button on the `/login` page:

| Role | Full Name | Username / Email | Password | Assigned Organization |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | Dr. Arthur Pendelton | `admin` / `admin@college.edu` | `Admin@123` | *All Campus Clubs* |
| **Coordinator** | David Kim | `coding_lead` / `coding_lead@college.edu` | `Coord@123` | **Coding Club** |
| **Coordinator** | Sophia Patel | `ai_lead` / `ai_lead@college.edu` | `Coord@123` | **AI & ML Club** |
| **Coordinator** | Ethan Hunt | `robotics_lead` / `robotics_lead@college.edu` | `Coord@123` | **Robotics Club** |
| **Coordinator** | Aaliyah Ross | `cultural_lead` / `cultural_lead@college.edu` | `Coord@123` | **Cultural Club** |
| **Coordinator** | Leo Martinez | `photo_lead` / `photo_lead@college.edu` | `Coord@123` | **Photography Club** |
| **Coordinator** | Zack Taylor | `eclub_lead` / `eclub_lead@college.edu` | `Coord@123` | **Entrepreneurship Club** |
| **Student** | Alex Rivera | `alex` / `alex@college.edu` | `Student@123` | CS 2nd Year |
| **Student** | Priya Sharma | `priya` / `priya@college.edu` | `Student@123` | IT 3rd Year |
| **Student** | Marcus Chen | `marcus` / `marcus@college.edu` | `Student@123` | Mech 1st Year |
| **Student** | Sarah Jenkins | `sarah` / `sarah@college.edu` | `Student@123` | ECE 2nd Year |

---

## 🧪 Running Automated Tests

Run the complete test suite to verify routes, model integrity, and RBAC security:

```bash
python -m unittest test_app.py -v
```

All tests run against live database scenarios (joining, event RSVP, capacity limits, user deactivations).

---

## 📸 Screenshots & UI Preview

* **Landing Page**: Modern hero section with live platform metrics, featured club cards, and event countdowns.
* **Student Hub**: Clean dashboard displaying enrolled organizations, registered passes, and bulletin feeds.
* **Coordinator Desk**: Comprehensive event editor, member roster management, and RSVP check-in tracking.
* **Admin Control Center**: Global oversight with user status toggling, role assignment, and club creation.

---

## 👥 Project Development Team & Module Distribution

This project was developed collaboratively by a **3-Member Engineering Team** with clearly segregated module ownership and architectural responsibilities:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   COLLEGE CLUB MANAGEMENT SYSTEM (3-MEMBER TEAM)                  │
├─────────────────────────┬────────────────────────────┬───────────────────────────┤
│    MEMBER 1 (LEAD)      │          MEMBER 2          │         MEMBER 3          │
│ Full-Stack & DB Arch    │      Frontend & UI/UX      │     Modules, Events & QA  │
├─────────────────────────┼────────────────────────────┼───────────────────────────┤
│ • Database ORM Models   │ • Collegiate Design System │ • Student RSVP & Passes   │
│ • Authentication & RBAC │ • Master Layout & Toasts   │ • Event Lifecycle Engine  │
│ • Admin Control Center  │ • Landing Page & Metrics   │ • Coordinator Workspace   │
│ • Data Seeder & API     │ • Search & DOM JS Logic    │ • Integration Test Suite  │
└─────────────────────────┴────────────────────────────┴───────────────────────────┘
```

### 📋 Detailed Member Assignment Matrix

| # | Team Member | Primary Role | Assigned Modules & Technical Contributions |
| :- | :--- | :--- | :--- |
| **1** | **Bhagath Shankar** *(Lead)* | **Full-Stack & Database Architect** | • Designed relational database schema in `models.py` (`User`, `Club`, `Membership`, `Event`, `EventRegistration`, `Announcement`)<br>• Implemented secure session-based authentication & RBAC decorators (`@login_required`, `@role_required`) in `app.py`<br>• Built Admin Control Center (`/admin/dashboard`, `/admin/users`, `/admin/clubs`) with role switching and user deactivation<br>• Created automatic database seeding pipeline with demo entities and test credentials |
| **2** | **Team Member 2** | **Frontend & UI/UX Specialist** | • Designed modern custom collegiate UI theme in `static/css/style.css` using modern gradients, glassmorphism, and responsive CSS variables<br>• Developed master layout `templates/base.html` with responsive navbar, floating toast alerts, and footer<br>• Crafted interactive landing page `templates/index.html` featuring real-time hero metrics, spotlight cards, and dynamic bulletins<br>• Wrote JavaScript utilities in `static/js/main.js` for live search filtering and 1-click test fill chips |
| **3** | **Team Member 3** | **Modules & Quality Assurance Engineer** | • Implemented Student Hub (`/student/dashboard`, `/student/my_clubs`, `/student/my_events`) with digital ticket pass generation (`PASS #TKT-...`)<br>• Built Coordinator Workspace (`/coordinator/*`) for event capacity tracking, member promotion, and attendee check-in management<br>• Developed campus-wide Announcement & Bulletin Broadcasting System (`/announcements`) with priority tagging (`Normal`, `Important`, `Urgent`)<br>• Authored automated integration test suite in `test_app.py` verifying model integrity and RBAC permissions |

---

## 🔮 Future Enhancements

* QR code generation for digital event ticket check-ins.
* Email notifications for new announcements and event reminders via SMTP.
* Club budget tracking and expense reimbursement workflows.
* Certificate generation for active participants and workshop attendees.

