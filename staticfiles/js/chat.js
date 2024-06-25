// static/js/chat.js
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
    return getCookie('csrftoken');
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", updateCsrfToken());
        }
    }
});

function login() {
    $.ajax({
        url: '/login/',
        type: 'POST',
        data: {
            username: $('#username').val(),
            password: $('#password').val()
        },
        success: function(response) {
            if (response.success) {
                $('#login-dialog').hide();
                $('#chat-container').removeClass('hidden');
            } else {
                $('#login-error').text('Invalid username or password');
            }
        },
        error: function(xhr, status, error) {
            console.error('Login error:', xhr.responseText);
            $('#login-error').text('An error occurred. Please try again.');
        }
    });
}

function logout() {
    $.ajax({
        url: '/logout/',
        type: 'POST',
        success: function(response) {
            if (response.success) {
                $('#chat-container').addClass('hidden');
                $('#login-dialog').show();
            } else {
                console.error('Logout failed:', response);
            }
        },
        error: function(xhr, status, error) {
            console.error('Logout error:', xhr.responseText);
        }
    });
}

function sendMessage() {
    var userInput = $('#user-input').val();
    if (userInput.trim() === '') return;

    appendMessage('You', userInput, 'user-message');
    $('#user-input').val('');

    $.ajax({
        url: '',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({'user_input': userInput}),
        success: function(response) {
            console.log('Success:', response);
            appendMessage('Bot', response.response, 'bot-message');
        },
        error: function(xhr, status, error) {
            console.error('Error:', xhr.responseText);
            if (xhr.status === 403) {
                alert('Your session has expired. Please log in again.');
                $('#chat-container').addClass('hidden');
                $('#login-dialog').show();
            } else {
                appendMessage('Error', error, 'bot-message');
            }
        }
    });
}

function appendMessage(sender, message, className) {
    $('#chat-messages').append('<div class="message ' + className + '"><strong>' + sender + ':</strong> ' + message + '</div>');
    $('#chat-messages').scrollTop($('#chat-messages')[0].scrollHeight);
}

$(document).ready(function() {
    $('#logout-button').click(function(e) {
        e.preventDefault();
        logout();
    });

    $('#send-button').click(sendMessage);

    $('#user-input').keypress(function(e) {
        if(e.which == 13) {
            sendMessage();
        }
    });
});