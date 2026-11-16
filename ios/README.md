# Modul iOS

APK injection tidak berlaku di iOS. Untuk perangkat iPhone gunakan tiga jalur berikut,
semuanya di-generate dari halaman Build:

## 1. Web Clip (paling cepat)
Profil `.mobileconfig` berisi ikon + URL ke halaman agent web C2. Sekali tap install,
ikon muncul di home screen target. Cocok untuk kontrol ringan: lokasi, kamera, mic,
notifikasi, screenshot.

## 2. Shortcut Otomasi
`shortcut.json` diimpor ke app Shortcuts. Menjalankan: kirim lokasi, IP, model,
baterai ke endpoint C2 tiap interval yang diizinkan iOS.

## 3. Sideload (full akses)
Untuk kontrol penuh gunakan build IPA terpisah (butuh macOS + sertifikat).
Struktur target iOS ada di `ios/target/` (Xcode project placeholder).

Batas platform yang perlu dipahami:
- Screen mirroring penuh butuh sesi aktif (iOS membatasi background capture)
- Dump SMS/iCloud terbatas pada yang diekspos API publik
- Kontak & galeri butuh izin manual satu kali
