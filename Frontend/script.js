const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const chatLog = document.getElementById('chat-log');

sendButton.addEventListener('click', async () => {
    const message = messageInput.value.trim();
    const backend_url = '';
    if (message) {
        try {
            const response = await fetch(backend_url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: message })
            });
            // const response = await fetch('mock-lambda.json');
            const data = await response.json();
            const responseMessage = data.response.output.text;
            // const responseMessage = data.responseMessage.replace('{{message}}', message);;
            console.log(responseMessage);
            chatLog.innerHTML += `<p>You: ${message}</p><p>Bot: ${responseMessage}</p>`;
            messageInput.value = '';
        } catch (error) {
            console.error(error);
        }
    }
});