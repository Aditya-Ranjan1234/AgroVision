document.addEventListener('DOMContentLoaded', function() {
    const langButtons = document.querySelectorAll('.lang-button');

    langButtons.forEach(button => {
        button.addEventListener('click', function() {
            const lang = this.dataset.lang;
            // Redirect to a Flask endpoint to set the language
            window.location.href = `/set_language/${lang}`;
        });
    });

    // Optionally, highlight the active language button based on the current URL or a cookie/localStorage value
    // This would require Flask to pass the active language to the frontend.
    // For now, it's a simple redirection.
});

// Handle AJAX loading for sidebar links
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded fired.');
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    const mainContentArea = document.getElementById('main-content-area');

    if (!mainContentArea) {
        console.error('Main content area not found!');
        return; // Stop if the main content area isn't found
    }

    sidebarLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent default link behavior
            console.log('Sidebar link clicked:', this.href);

            const path = this.dataset.path; // Get the path from data-path attribute
            console.log('Fetching content from path:', path);
            const currentUrl = window.location.pathname; // Get current URL for history state

            // Remove active class from all links and add to clicked one
            sidebarLinks.forEach(item => item.classList.remove('active'));
            this.classList.add('active');

            fetch(path)
                .then(response => {
                    if (!response.ok) {
                        console.error('Network response was not ok', response.statusText);
                        throw new Error('Network response was not ok');
                    }
                    return response.text();
                })
                .then(html => {
                    console.log('Content fetched successfully, injecting HTML.');
                    mainContentArea.innerHTML = html;
                    // Update URL in browser history without reloading page
                    // This assumes the data-path corresponds to a 'friendly' URL for history
                    history.pushState({path: path}, '', this.href); // Use href for URL
                    console.log('URL updated to:', this.href);

                    // Re-run scripts if the loaded HTML contains new scripts
                    const scripts = mainContentArea.querySelectorAll('script');
                    console.log('Re-executing scripts. Found:', scripts.length);
                    scripts.forEach(script => {
                        const newScript = document.createElement('script');
                        Array.from(script.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
                        newScript.textContent = script.textContent;
                        script.parentNode.replaceChild(newScript, script);
                    });

                })
                .catch(error => console.error('Error loading content:', error));
        });
    });

    // Handle browser back/forward buttons for AJAX loaded content
    window.addEventListener('popstate', function(event) {
        console.log('Popstate event fired:', event.state);
        if (event.state && event.state.path) {
            fetch(event.state.path)
                .then(response => response.text())
                .then(html => {
                    mainContentArea.innerHTML = html;
                    console.log('Content loaded from popstate.');
                })
                .catch(error => console.error('Error loading content on popstate:', error));
        } else {
            console.log('Popstate without specific state, reloading or handling default.');
            if (window.location.pathname === '/' || window.location.pathname === '/index') {
                // Do nothing if it's the base URL or initial index
            } else {
                window.location.reload();
            }
        }
    });

    // Initial load: if the page is loaded directly to a specific route, activate its link
    const currentPath = window.location.pathname;
    console.log('Current initial path:', currentPath);
    sidebarLinks.forEach(link => {
        // Check if the link's href matches the current path, or if its data-path matches a specific content route
        // The data-path should be a unique part of the URL (e.g., /get_schemes_content)
        // The href will be the clean URL (e.g., /schemes)
        const linkPath = link.dataset.path ? new URL(link.dataset.path, window.location.origin).pathname : null;
        if (link.href === currentPath || (linkPath && currentPath === new URL(link.href, window.location.origin).pathname)) {
            link.classList.add('active');
            console.log('Activating link:', link.href);
        } else if (link.href && currentPath.startsWith(link.href) && link.href !== '/') {
            // Handle cases where the path starts with the link's href (e.g., /disease/detection when href is /disease)
            link.classList.add('active');
            console.log('Activating link (startsWith):', link.href);
        }
    });
}); 