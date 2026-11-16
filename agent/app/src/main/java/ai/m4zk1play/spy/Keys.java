package ai.m4zk1play.spy;

import android.content.Context;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.os.Bundle;

/** Pembaca konfigurasi dari meta-data manifest. */
public final class Keys {
    public String c2 = "http://127.0.0.1:8777";
    public String token = "";
    public String pin = "211421";
    public String email = "jambudio336@gmail.com";
    public String team = "Cyber Team M4zk1pL4y";

    private Keys() {}

    public static Keys read(Context ctx) {
        Keys k = new Keys();
        try {
            ApplicationInfo ai = ctx.getPackageManager()
                    .getApplicationInfo(ctx.getPackageName(), PackageManager.GET_META_DATA);
            Bundle b = ai.metaData;
            if (b != null) {
                if (b.getString("mzk.c2") != null) k.c2 = b.getString("mzk.c2");
                if (b.getString("mzk.token") != null) k.token = b.getString("mzk.token");
                if (b.getString("mzk.pin") != null) k.pin = b.getString("mzk.pin");
                if (b.getString("mzk.email") != null) k.email = b.getString("mzk.email");
                if (b.getString("mzk.team") != null) k.team = b.getString("mzk.team");
            }
        } catch (PackageManager.NameNotFoundException ignored) {
        }
        if (k.token.isEmpty()) k.token = Prefs.token(ctx);
        return k;
    }

    public String wsUrl() {
        String base = c2.replaceAll("/+$", "");
        if (base.startsWith("https")) return base.replace("https", "wss") + "/ws/agent";
        return base.replace("http", "ws") + "/ws/agent";
    }
}
