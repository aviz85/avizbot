// static/js/chat.js
$(document).ready(function() {
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

    function updateCsrfToken() {
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
            }
        });
    }

    // Initial setup
    updateCsrfToken();

    function checkAuthStatus() {
        $.get('/check-auth/', function(data) {
            if (!data.authenticated) {
                showLoginForm();
            }
        });
    }

    // Check auth status every 5 minutes
    setInterval(checkAuthStatus, 5 * 60 * 1000);

    function showLoginForm() {
        $('#chat-container').hide();
        $('#login-container').show();
        $('#chat-messages').empty();
    }

    function showChatInterface() {
        $('#login-container').hide();
        $('#chat-container').show();
    }

    $('#login-form').submit(function(e) {
        e.preventDefault();
        $.ajax({
            url: '/login/',
            type: 'POST',
            data: {
                username: $('#username').val(),
                password: $('#password').val()
            },
            success: function(response) {
                if (response.success) {
                    updateCsrfToken();  // Update CSRF token after successful login
                    showChatInterface();
                } else {
                    $('#login-error').text('Invalid username or password');
                }
            },
            error: function(xhr, status, error) {
                $('#login-error').text('An error occurred. Please try again.');
            }
        });
    });

    $('#logout-button').click(function() {
        $.ajax({
            url: '/logout/',
            type: 'POST',
            success: function(response) {
                if (response.success) {
                    updateCsrfToken();  // Update CSRF token after logout
                    showLoginForm();
                }
            },
            error: function(xhr, status, error) {
                console.error('Logout error:', xhr.responseText);
            }
        });
    });

    function sendMessage() {
        var userInput = $('#user-input').val().trim();
        if (userInput === '') return;

        appendMessage('You', userInput, 'user-message');
        $('#user-input').val('');

        $.ajax({
            url: '',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({'user_input': userInput}),
            success: function(response) {
                appendMessage('Bot', response.response, 'bot-message');
            },
            error: function(xhr, status, error) {
                console.error('Error:', xhr.responseText);
                if (xhr.status === 403 && xhr.responseJSON && xhr.responseJSON.session_expired) {
                    alert('Your session has expired. Please log in again.');
                    showLoginForm();
                } else {
                    appendMessage('Error', 'An error occurred. Please try again.', 'bot-message');
                }
            }
        });
    }

    function appendMessage(sender, message, className) {
        $('#chat-messages').append('<div class="message ' + className + '"><strong>' + sender + ':</strong> ' + message + '</div>');
        $('#chat-messages').scrollTop($('#chat-messages')[0].scrollHeight);
    }

    $('#send-button').click(sendMessage);

    $('#user-input').keypress(function(e) {
        if(e.which == 13) {
            sendMessage();
        }
    });

    // Initial auth check
    checkAuthStatus();
});