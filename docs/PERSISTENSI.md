# Persistence

## Berlapis, urutan aktif

1. `BootReceiver` — BOOT_COMPLETED, LOCKED_BOOT_COMPLETED, MY_PACKAGE_REPLACED,
   QUICKBOOT_POWERON, USER_PRESENT, CONNECTIVITY_CHANGE, TIME_SET
2. `AlarmManager` — tiap 15 menit, `ELAPSED_REALTIME_WAKEUP`
3. `JobScheduler` — periodik 15 menit, `setPersisted(true)` (tahan reboot)
4. `START_STICKY` + `onTaskRemoved` → re-arm
5. `BootProvider` (ContentProvider) — dipanggil saat proses app pertama kali naik
6. Device Admin — `onDisableRequested` + PIN

## Batas nyata

| Kejadian | Hasil |
|---|---|
| Reboot | **Hidup lagi** (rantai 1–5) |
| App di-force stop manual | Hidup lagi setelah dibuka, alarm/job bangunkan |
| Dibersihkan dari recents | Hidup (foreground service) |
| Uninstall | Dicegah Device Admin + PIN 211421 |
| Setelan pabrik | **Mati** — kecuali dipasang sebagai app sistem (`scripts/system-install.sh`) |

Setelan pabrik menghapus semua app user. Tidak ada cara tanpa root
atau tanpa Google Auto Backup. Kalau perangkat root, pakai `system-install.sh`.
