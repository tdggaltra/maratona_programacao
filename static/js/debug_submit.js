# static/js/debug_submit.js (CRIAR ESTE ARQUIVO)

function debugSubmit(challengeId) {
    const testCode = `public class Test {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}`;
    
    console.log('=== DEBUG SUBMIT ===');
    console.log('Challenge ID:', challengeId);
    console.log('Code:', testCode);
    
    // Primeiro, testar endpoint de debug
    fetch('/debug/submit/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            code: testCode
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('=== DEBUG RESPONSE ===');
        console.log(data);
        
        // Se debug passou, testar submissão real
        if (data.json_valid) {
            console.log('=== TESTING REAL SUBMIT ===');
            return fetch(`/challenge/${challengeId}/submit-debug/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    code: testCode
                })
            });
        }
    })
    .then(response => {
        if (response) {
            console.log('Real submit status:', response.status);
            return response.json();
        }
    })
    .then(data => {
        if (data) {
            console.log('=== REAL SUBMIT RESPONSE ===');
            console.log(data);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function getCsrfToken() {
    // Tenta diferentes métodos para pegar o CSRF token
    const token = document.querySelector('meta[name="csrf-token"]')?.content ||
                  document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                  getCookie('csrftoken');
    return token;
}

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
