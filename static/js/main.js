/**
 * College Club Management System - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Initialize Bootstrap Tooltips & Popovers
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 2. Auto-dismiss Flash Alerts after 5 seconds
    const flashAlerts = document.querySelectorAll('.flash-container .alert');
    flashAlerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // 3. Quick Login Demo Helper
    window.quickLogin = function (username, password) {
        const usernameInput = document.getElementById('username');
        const passwordInput = document.getElementById('password');
        if (usernameInput && passwordInput) {
            usernameInput.value = username;
            passwordInput.value = password;
            // Add a brief glow effect
            usernameInput.classList.add('border-primary');
            passwordInput.classList.add('border-primary');
            setTimeout(() => {
                usernameInput.classList.remove('border-primary');
                passwordInput.classList.remove('border-primary');
            }, 800);
        }
    };

    // 4. Club Filtering & Search
    const clubSearchInput = document.getElementById('clubSearchInput');
    const categoryButtons = document.querySelectorAll('.club-category-btn');
    const clubCards = document.querySelectorAll('.club-card-item');

    if (clubCards.length > 0) {
        let activeCategory = 'all';

        function filterClubs() {
            const query = clubSearchInput ? clubSearchInput.value.toLowerCase().trim() : '';
            let visibleCount = 0;

            clubCards.forEach(function (card) {
                const name = card.getAttribute('data-name')?.toLowerCase() || '';
                const category = card.getAttribute('data-category')?.toLowerCase() || '';
                const desc = card.getAttribute('data-desc')?.toLowerCase() || '';

                const matchesQuery = name.includes(query) || desc.includes(query);
                const matchesCategory = activeCategory === 'all' || category === activeCategory;

                if (matchesQuery && matchesCategory) {
                    card.parentElement.style.display = 'block';
                    visibleCount++;
                } else {
                    card.parentElement.style.display = 'none';
                }
            });

            const noResults = document.getElementById('noClubResults');
            if (noResults) {
                noResults.style.display = visibleCount === 0 ? 'block' : 'none';
            }
        }

        if (clubSearchInput) {
            clubSearchInput.addEventListener('input', filterClubs);
        }

        categoryButtons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                categoryButtons.forEach(b => b.classList.remove('active', 'btn-primary'));
                categoryButtons.forEach(b => b.classList.add('btn-outline-secondary'));
                this.classList.remove('btn-outline-secondary');
                this.classList.add('btn-primary', 'active');

                activeCategory = this.getAttribute('data-category').toLowerCase();
                filterClubs();
            });
        });
    }

    // 5. Event Filtering & Search
    const eventSearchInput = document.getElementById('eventSearchInput');
    const eventCards = document.querySelectorAll('.event-card-item');

    if (eventCards.length > 0 && eventSearchInput) {
        eventSearchInput.addEventListener('input', function () {
            const query = this.value.toLowerCase().trim();
            let visibleCount = 0;

            eventCards.forEach(function (card) {
                const title = card.getAttribute('data-title')?.toLowerCase() || '';
                const club = card.getAttribute('data-club')?.toLowerCase() || '';
                const location = card.getAttribute('data-location')?.toLowerCase() || '';

                if (title.includes(query) || club.includes(query) || location.includes(query)) {
                    card.parentElement.style.display = 'block';
                    visibleCount++;
                } else {
                    card.parentElement.style.display = 'none';
                }
            });

            const noResults = document.getElementById('noEventResults');
            if (noResults) {
                noResults.style.display = visibleCount === 0 ? 'block' : 'none';
            }
        });
    }
});
