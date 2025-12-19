import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.io.*;
import java.net.*;

public class ClientGUI {
    private JFrame frame;
    private JTextArea logArea;
    private JLabel speedLabel, battLabel, dirLabel;
    private Socket socket;
    private BufferedReader in;
    private PrintWriter out;
    private String serverIp;
    private int serverPort;
    private boolean authenticated = false;
    private String role = "observer";

    //  moved here — inside class
    private WebSocketClientHandler webSocketClient;

    public ClientGUI(String serverIp, int serverPort) {
        this.serverIp = serverIp;
        this.serverPort = serverPort;
        build();
    }

    private void build() {
        frame = new JFrame("Cliente Metro - Java");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(600, 400);

        JPanel top = new JPanel();
        ButtonGroup bg = new ButtonGroup();
        JRadioButton obs = new JRadioButton("Observer");
        obs.setSelected(true);
        JRadioButton adm = new JRadioButton("Admin");
        bg.add(obs);
        bg.add(adm);
        top.add(obs);
        top.add(adm);
        JButton connectBtn = new JButton("Conectar");
        top.add(connectBtn);
        frame.add(top, BorderLayout.NORTH);

        JPanel center = new JPanel(new GridLayout(3, 2));
        center.add(new JLabel("Velocidad:"));
        speedLabel = new JLabel("-");
        center.add(speedLabel);
        center.add(new JLabel("Batería:"));
        battLabel = new JLabel("-");
        center.add(battLabel);
        center.add(new JLabel("Dirección:"));
        dirLabel = new JLabel("-");
        center.add(dirLabel);
        frame.add(center, BorderLayout.CENTER);

        JPanel cmds = new JPanel();
        JButton spup = new JButton("SPEEDUP");
        JButton spdown = new JButton("SLOWDOWN");
        JButton stop = new JButton("STOPNOW");
        JButton start = new JButton("STARTNOW");
        JButton listu = new JButton("LISTUSERS");
        cmds.add(spup);
        cmds.add(spdown);
        cmds.add(stop);
        cmds.add(start);
        cmds.add(listu);
        frame.add(cmds, BorderLayout.SOUTH);

        logArea = new JTextArea();
        JScrollPane sp = new JScrollPane(logArea);
        sp.setPreferredSize(new Dimension(580, 120));
        frame.add(sp, BorderLayout.SOUTH);

        connectBtn.addActionListener(e -> {
            if (adm.isSelected()) role = "admin"; else role = "observer";
            connect();
        });
        spup.addActionListener(e -> sendCommand("SPEEDUP"));
        spdown.addActionListener(e -> sendCommand("SLOWDOWN"));
        stop.addActionListener(e -> sendCommand("STOPNOW"));
        start.addActionListener(e -> sendCommand("STARTNOW"));
        listu.addActionListener(e -> sendListUsers());

        frame.addWindowListener(new WindowAdapter() {
            @Override
            public void windowClosing(WindowEvent e) {
                closeConnections();
            }
        });

        frame.setVisible(true);
    }

    private void connect() {
        try {
            socket = new Socket(serverIp, serverPort);
            in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
            out = new PrintWriter(socket.getOutputStream(), true);
            appendLog("Conectado a " + serverIp + ":" + serverPort);
            out.println("ROLE|" + role);
            if (role.equals("admin")) {
                String user = JOptionPane.showInputDialog(frame, "Usuario:");
                String pass = JOptionPane.showInputDialog(frame, "Pass:");
                out.println("AUTH|user=" + user + ";pass=" + pass);
            }
            new Thread(() -> {
                try {
                    String line;
                    while ((line = in.readLine()) != null) handleMessage(line);
                } catch (IOException ex) {
                    appendLog("Reader error: " + ex.getMessage());
                }
            }).start();
        } catch (Exception ex) {
            appendLog("Connect error: " + ex.getMessage());
        }
    }

    private void handleMessage(String msg) {
        appendLog("Recibido: " + msg);
        if (msg.startsWith("RESPONSE|OK")) authenticated = true;
        else if (msg.startsWith("TELEMETRY|")) {
            String body = msg.substring("TELEMETRY|".length());
            String[] parts = body.split(";");
            for (String kv : parts) {
                if (kv.contains("=")) {
                    String[] a = kv.split("=", 2);
                    String k = a[0], v = a[1];
                    switch (k) {
                        case "speed": speedLabel.setText(v + " km/h"); break;
                        case "battery": battLabel.setText(v + " %"); break;
                        case "direction": dirLabel.setText(v); break;
                    }
                }
            }
        } else if (msg.startsWith("RESPONSE|USERS;")) {
            String users = msg.substring("RESPONSE|USERS;".length());
            JOptionPane.showMessageDialog(frame, "Usuarios: " + users);
        }
    }

    private void sendCommand(String cmd) {
        if (out == null) {
            appendLog("No conectado");
            return;
        }
        if (!authenticated) {
            appendLog("No autenticado como admin");
            return;
        }
        out.println("COMMAND|" + cmd);
        appendLog("Enviado: " + cmd);
    }

    private void sendListUsers() {
        if (out == null) {
            appendLog("No conectado");
            return;
        }
        if (!authenticated) {
            appendLog("No autenticado como admin");
            return;
        }
        out.println("LISTUSERS");
    }

    private void appendLog(String s) {
        SwingUtilities.invokeLater(() -> logArea.append(s + "\n"));
    }

    private void closeConnections() {
        try {
            if (socket != null) socket.close();
            if (webSocketClient != null) webSocketClient.close();
        } catch (IOException ignored) {}
    }

    // previously illegal code moved into a method
    public void sendWebSocketMessage(String msg) {
        if (webSocketClient != null && webSocketClient.isOpen()) {
            webSocketClient.send(msg);
        } else {
            appendLog("WebSocket no conectado");
        }
    }
	public static void main(String[] args) {
	    String ip = "127.0.0.1";
	    int port = 5000;

	    if (args.length >= 2) {
	        ip = args[0];
	        port = Integer.parseInt(args[1]);
	    }

	    final String finalIp = ip;
	    final int finalPort = port;

	    SwingUtilities.invokeLater(() -> new ClientGUI(finalIp, finalPort));
	}
}