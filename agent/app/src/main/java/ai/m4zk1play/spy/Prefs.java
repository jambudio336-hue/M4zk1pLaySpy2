package ai.m4zk1play.spy;

import android.content.Context;
import android.content.SharedPreferences;

import java.util.UUID;

public final class Prefs {
    private static final String FILE = "mzk";
    private static SharedPreferences sp(Context c) {
        return c.getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }
    public static String token(Context c) {
        String t = sp(c).getString("token", "");
        if (t.isEmpty()) {
            t = UUID.randomUUID().toString().replace("-", "");
            sp(c).edit().putString("token", t).apply();
        }
        return t;
    }
    public static void put(Context c, String k, String v) {
        sp(c).edit().putString(k, v).apply();
    }
    public static String get(Context c, String k, String def) {
        return sp(c).getString(k, def);
    }
    public static boolean flag(Context c, String k) {
        return sp(c).getBoolean(k, false);
    }
    public static void setFlag(Context c, String k, boolean v) {
        sp(c).edit().putBoolean(k, v).apply();
    }
}
