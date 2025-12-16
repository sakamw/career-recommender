// Form validation helper
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Copy share summary (recommendation detail)
    document.querySelectorAll('[data-copy-share]').forEach(btn => {
        btn.addEventListener('click', async function() {
            const text = this.getAttribute('data-share-text') || '';
            if (!text) return;

            try {
                await navigator.clipboard.writeText(text);
                const original = this.textContent;
                this.textContent = 'Copied!';
                setTimeout(() => { this.textContent = original; }, 1200);
            } catch (e) {
                // Fallback for older browsers
                const ta = document.createElement('textarea');
                ta.value = text;
                ta.style.position = 'fixed';
                ta.style.top = '-9999px';
                document.body.appendChild(ta);
                ta.focus();
                ta.select();
                try {
                    document.execCommand('copy');
                    const original = this.textContent;
                    this.textContent = 'Copied!';
                    setTimeout(() => { this.textContent = original; }, 1200);
                } finally {
                    document.body.removeChild(ta);
                }
            }
        });
    });
});

// Helper function to format dates (if needed)
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

