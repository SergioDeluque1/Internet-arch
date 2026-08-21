const WebSocket = require('ws');

// Replace with your AWS public IP
const ws = new WebSocket('ws://YOUR_AWS_PUBLIC_IP:8080');

ws.on('open', () => {
    console.log('Connected to server');
    ws.send('Hello from client!');
});

ws.on('message', (data) => {
    console.log('Received:', data.toString());
});

ws.on('error', (error) => {
    console.error('WebSocket error:', error);
});

ws.on('close', () => {
    console.log('Disconnected from server');
});