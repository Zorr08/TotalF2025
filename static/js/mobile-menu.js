document.addEventListener('DOMContentLoaded', () => {
    const menuButton = document.getElementById('menu-button');
    const menu = document.getElementById('menu');
    
    function toggleMenu() {
        if (!menu || !menuButton) return;
        
        const isExpanded = menuButton.getAttribute('aria-expanded') === 'true';
        menuButton.setAttribute('aria-expanded', !isExpanded);
        
        if (isExpanded) {
            // Close menu
            menu.style.transform = 'translateX(100%)';
            setTimeout(() => {
                menu.classList.add('hidden');
                menuButton.style.display = 'block'; // Show button
            }, 300);
        } else {
            // Open menu
            menuButton.style.display = 'none'; // Hide button
            menu.classList.remove('hidden');
            requestAnimationFrame(() => {
                menu.style.transform = 'translateX(0)';
            });
        }
        
        // Prevent body scrolling when menu is open
        document.body.style.overflow = isExpanded ? 'auto' : 'hidden';
    }
    
    function closeMenu() {
        if (!menu || !menuButton) return;
        
        menuButton.setAttribute('aria-expanded', 'false');
        menu.style.transform = 'translateX(100%)';
        
        setTimeout(() => {
            menu.classList.add('hidden');
            menuButton.style.display = 'block'; // Show button
        }, 300);
        
        document.body.style.overflow = 'auto';
    }
    
    // Handle menu button clicks
    if (menuButton) {
        menuButton.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleMenu();
        });
    }
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!menu?.contains(e.target) && !menuButton?.contains(e.target)) {
            closeMenu();
        }
    });
    
    // Handle menu item clicks
    const menuLinks = document.querySelectorAll('.menu-link');
    menuLinks.forEach(link => {
        link.addEventListener('click', () => {
            closeMenu();
        });
    });
    
    // Setup gameweek JSON button
    const gameweekJsonBtn = document.getElementById('gameweek-json-btn');
    if (gameweekJsonBtn) {
        gameweekJsonBtn.addEventListener('click', () => {
            window.location.href = '/api/gameweek';
        });
    }
    
    // Initialize menu state
    if (menu && menuButton) {
        menu.style.transform = 'translateX(100%)';
        menu.classList.add('hidden');
        menuButton.style.display = 'block';
    }
});