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