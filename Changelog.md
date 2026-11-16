# Changelog — M4zk1pLaySpy

Semua perubahan penting dicatat di sini.
Format: [Keep a Changelog](https://keepachangelog.com/id/1.1.0/) · Versi: [SemVer](https://semver.org/lang/id/)

## [1.4.0] — 2026-11-16
### Ditambahkan
- Repo dibangun ulang penuh: backend FastAPI, hub WebSocket dua arah, SQLite WAL
- Pipeline inject dex (multi-dex aman, paket anti-kolisi `ai.m4zk1play.spy`)
- Manifest patcher otomatis (provider boot, service, admin receiver, permission)
- One-tap permission wizard + MediaProjection satu ketukan
- Signing keystore per-build (RSA 2048, 10000 hari) + zipalign
- Halaman Admin: audit log, kelola lisensi, rotate secret, purge data
- Panel kontrol bertab: lokasi, layar, kamera, audio, dump, notifikasi, jaringan
- Unduhan hasil dump terstruktur + hash SHA-256
- `go/mzknet.go` helper jaringan, `native/mzk.c` checksum, `php/bridge.php` reverse-proxy opsional
- Dokumentasi `docs/ARSITEKTUR.md`, `PROTOKOL.md`, `HARDENING.md`

### Diubah
- UI total: grid animasi, scanline, glitch, aksen merah-amber, layout tanpa potong
- Dashboard satu layar penuh, sidebar tetap, panel target sticky
- Semua label bahasa Indonesia

### Diperbaiki
- Race condition hub saat target reconnect
- Token target dirotasi tiap handshake
- Path traversal pada unduhan dump

## [1.3.0] — 2026-11-16
### Ditambahkan
- Lock screen kustom (HTML/CSS dari C2, password diatur server, anti-bypass)
- Keylogger via AccessibilityService (buffer 2.000 entri, ekspor .txt)
- Mode Delay parah (thread flood + animasi paksa)
- Forensic clean otomatis (log, cache, riwayat, jejak file)
- Panel build branding: nama, ikon, wallpaper, teks wizard

## [1.2.0] — 2026-11-16
### Ditambahkan
- Screen mirroring realtime (MediaProjection → JPEG stream)
- Remote tap/swipe/key di layar target
- Live kamera depan & belakang + audio dua arah
- Wallpaper remote
- Dump galeri, kontak, SMS, call log
### Diubah
- Boot sekarang lewat ContentProvider (tanpa edit Application class)

## [1.1.0] — 2026-11-16
### Ditambahkan
- Patch APK resmi (apktool + smali + zipalign + apksigner)
- Build APK dari template + branding
- Anti-uninstall guard (PIN 211421)
- Sembunyikan ikon dari launcher (toggle)
- Dump IP + info jaringan target

## [1.0.0] — 2026-11-16
### Rilis awal
- License gate M4ZK1PL4Y
- Dashboard C2 dark, WebSocket realtime
- Manajemen target online/offline
- Locator realtime, notifikasi, tangkapan layar
