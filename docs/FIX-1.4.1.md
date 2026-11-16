# Catatan Perbaikan 1.4.1

## Yang diperbaiki

1. **`security.client_ip_from_ws()` hilang** — `main.py` memanggilnya saat handshake
   agent, tapi fungsinya tidak ada. Agent crash → target tidak pernah terdaftar.
   Ditambahkan + `kill_session()` untuk logout bersih.
2. **`AndroidManifest.xml` agent tanpa permission** — tidak ada satu pun
   `<uses-permission>`, jadi wizard izin tidak bisa meminta apa pun. Ditambahkan
   34 izin termasuk `FOREGROUND_SERVICE_*` yang wajib di API 34.
3. **Ikon `@mipmap/ic_launcher` tidak ada** — `res/` hanya punya `drawable/`.
   Referensi diubah ke `@drawable/ic_launcher_fg`.
4. **`BootProvider` tidak dipicu saat boot** — manifest menunjuk receiver ke
   `ai.m4zk1play.spy.Keys` yang bukan `BroadcastReceiver`. Dibuat `BootReceiver.java`
   dan manifest diarahkan ke sana.
5. **`PlayerActivity` tidak terdaftar** — `Router.play()` start activity yang tidak
   ada di manifest → `ActivityNotFoundException`. Sudah didaftarkan.
6. **`agent/prebuilt/` tidak ada** — pipeline build selalu gagal. Folder + README
   + `.gitkeep` dibuat, `.gitignore` disesuaikan agar APK prebuilt bisa di-commit.
7. **`time.sleep()` di `api_control.wait()`** — memblokir event loop. Diganti
   `asyncio.sleep()`.
8. **`builder.py`** — `subprocess` diimpor di dalam fungsi, cek tool kurang,
   `/tmp` hardcoded. Dirapikan + `prebuilt()` dengan pesan jelas.
9. **`web/agent.html` tidak ada** — dirujuk `ios/mobileconfig` dan rute `/agent`
   di main.py. Dibuat.
10. **`/api/ios/beacon` tidak ada** — dibuat `server/api_ios.py` + router terdaftar.
11. **`MainActivity` pakai `checkSelfPermission` langsung** — crash di API 21/22.
    Diganti `ContextCompat` + `ActivityCompat`.
12. **`mzk_wizard` tidak ada di strings.xml** — wizard jatuh ke fallback. Ditambahkan.

## Setelah menimpa

```bash
rm -rf server/__pycache__
./scripts/verify.sh          # harus semua ADA
./scripts/build-agent.sh     # isi agent/prebuilt
./run.sh
