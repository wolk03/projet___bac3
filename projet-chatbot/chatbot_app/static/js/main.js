// Extrait de votre main.js ou d'un fichier JS chargé par chat.html

// ... (le code pour gérer le clic sur le bouton d'envoi, etc.)

async function sendMessage() {
    // ...
    try {
        // Appeler notre NOUVELLE route API Flask
        const response = await fetch('/ask_rag', { // <-- URL CORRIGÉE
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: question })
        });
        
        const data = await response.json();
        
        // Afficher la réponse
        updateLastBotMessage(data.answer); 

    } catch (error) {
        // ...
    }
}

// ... (les fonctions addMessage, updateLastBotMessage, etc.)