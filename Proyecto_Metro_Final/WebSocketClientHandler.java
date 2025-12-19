public class WebSocketClientHandler {
    public boolean isOpen() {
        return false;
    }

    public void send(String message) {
        System.out.println("Stub WebSocket send: " + message);
    }

    public void close() {
        System.out.println("Stub WebSocket closed");
    }
}

