// Store form states for each team member
const formStates = new Map();

document.addEventListener('DOMContentLoaded', function () {
    // Initialize Feather Icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }

    // Copyright Year Update
    function updateCopyrightYear() {
        const yearElement = document.getElementById('currentYear');
        if (yearElement) {
            const currentYear = new Date().getFullYear();
            yearElement.textContent = currentYear;
        }
    }
    updateCopyrightYear();

    // Update year when tab becomes visible
    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'visible') {
            updateCopyrightYear();
        }
    });

    // Video Modal Functionality
    function initVideoModal() {
        const videoModal = document.getElementById('videoModal');
        const playBtn = document.querySelector('.box-play-icon');
        const closeVideoBtn = document.querySelector('.close-modal');
        const videoFrame = document.getElementById('videoFrame');

        if (playBtn && videoModal && closeVideoBtn && videoFrame) {
            playBtn.addEventListener('click', () => {
                videoModal.style.display = 'block';
                document.body.style.overflow = 'hidden';
            });

            function closeVideoModal() {
                videoModal.style.display = 'none';
                document.body.style.overflow = 'auto';
                const videoSrc = videoFrame.src;
                videoFrame.src = '';
                videoFrame.src = videoSrc;
            }

            closeVideoBtn.addEventListener('click', closeVideoModal);
            videoModal.addEventListener('click', (e) => {
                if (e.target === videoModal) closeVideoModal();
            });
        }
    }

    // Team Modal Functionality
    function initTeamModal() {
        const teamModal = document.getElementById('teamModal');
        if (!teamModal) return;

        const modalImage = document.getElementById('modalImage');
        const modalName = document.getElementById('modalName');
        const modalTitle = document.getElementById('modalTitle');
        const modalDescription = document.getElementById('modalDescription');
        const modalRate = document.getElementById('modalRate');
        const closeTeamBtn = teamModal.querySelector('.close');
        const readMoreButtons = document.querySelectorAll('.read-more');

        function resetFormState() {
            const container = teamModal.querySelector('.request-teammate-container');
            if (!container) return;

            const wrapper = container.querySelector('.request-form-wrapper');
            const emailWrapper = wrapper.querySelector('.email-input-wrapper');
            const emailInput = emailWrapper.querySelector('.email-input');
            const requestButton = wrapper.querySelector('.request-service-btn');
            const successMessage = container.querySelector('.success-message');
            
            emailWrapper.style.display = 'none';
            emailInput.value = '';
            requestButton.textContent = 'Request for my services';
            wrapper.style.display = 'flex';
            wrapper.style.justifyContent = 'flex-start';
            successMessage.style.display = 'none';
            emailWrapper.classList.remove('focused');
        }

        // Read More Button Click Handlers
        readMoreButtons.forEach(button => {
            button.addEventListener('click', function (e) {
                e.preventDefault();
                const memberId = this.getAttribute('data-member-id');

                // Reset form state when opening new modal
                resetFormState();

                // Fetch member details
                fetch(`/team/member/${memberId}/`)
                    .then(response => response.json())
                    .then(data => {
                        if (modalImage) {
                            modalImage.src = data.image_url;
                            modalImage.alt = data.name;
                        }
                        if (modalName) modalName.textContent = data.name;
                        if (modalTitle) modalTitle.textContent = data.title;
                        if (modalDescription) modalDescription.textContent = data.description;
                        if (modalRate) modalRate.textContent = `$${Math.floor(data.hourly_rate)}`;

                        // Store the current member ID for form submission
                        teamModal.setAttribute('data-current-member', memberId);

                        teamModal.style.display = 'block';
                        document.body.style.overflow = 'hidden';
                    })
                    .catch(error => console.error('Error:', error));
            });
        });

        // Initialize Request Buttons
        initRequestButtons();

        // Close Button Handler
        if (closeTeamBtn) {
            closeTeamBtn.addEventListener('click', function () {
                teamModal.style.display = 'none';
                document.body.style.overflow = 'auto';
                resetFormState();
            });
        }

        // Click Outside Modal Handler
        window.addEventListener('click', function (event) {
            if (event.target === teamModal) {
                teamModal.style.display = 'none';
                document.body.style.overflow = 'auto';
                resetFormState();
            }
        });
    }

    // Initialize Request Buttons
    function initRequestButtons() {
        const requestButtons = document.querySelectorAll('.request-service-btn');
        
        requestButtons.forEach(button => {
            button.addEventListener('click', function () {
                const teamModal = document.getElementById('teamModal');
                const memberId = teamModal.getAttribute('data-current-member');
                const container = this.closest('.request-teammate-container');
                const wrapper = this.closest('.request-form-wrapper');
                const emailWrapper = wrapper.querySelector('.email-input-wrapper');
                const successMessage = container.querySelector('.success-message');

                if (emailWrapper.style.display === 'none') {
                    // Show email input
                    emailWrapper.style.display = 'block';
                    this.textContent = 'Request';
                    wrapper.style.justifyContent = 'flex-end';

                    // Setup email input animations
                    const emailInput = emailWrapper.querySelector('.email-input');
                    const emailLabel = emailWrapper.querySelector('.email-label');

                    emailInput.addEventListener('focus', () => {
                        emailWrapper.classList.add('focused');
                    });

                    emailInput.addEventListener('blur', () => {
                        if (!emailInput.value) {
                            emailWrapper.classList.remove('focused');
                        }
                    });
                } else {
                    handleFormSubmission(this, memberId);
                }
            });
        });
    }

    // Handle form submission
    function handleFormSubmission(button, memberId) {
        const wrapper = button.closest('.request-form-wrapper');
        const emailInput = wrapper.querySelector('.email-input');
        const successMessage = wrapper.nextElementSibling;

        if (!emailInput.value) {
            alert('Please enter your email');
            return;
        }

        const modalName = document.getElementById('modalName').textContent;
        const modalTitle = document.getElementById('modalTitle').textContent;

        fetch('/send-request-email/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                email: emailInput.value,
                memberName: modalName,
                memberTitle: modalTitle,
                memberId: memberId
            })
        })
        .then(response => response.json())
        .then(data => {
            wrapper.style.display = 'none';
            successMessage.style.display = 'block';
            
            formStates.set(memberId, {
                submitted: true,
                email: emailInput.value
            });
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error sending your request. Please try again.');
        });
    }

    // Global ESC key handler for all modals
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
            const videoModal = document.getElementById('videoModal');
            const teamModal = document.getElementById('teamModal');

            // Close video modal
            if (videoModal && videoModal.style.display === 'block') {
                closeVideoModal();
            }
            // Close team modal
            if (teamModal && teamModal.style.display === 'block') {
                teamModal.style.display = 'none';
                document.body.style.overflow = 'auto';
                resetFormState();
            }
        }
    });

    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Initialize all functionality
    initVideoModal();
    initTeamModal();
});