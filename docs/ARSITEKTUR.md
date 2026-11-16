# Arsitektur

Operator (browser) ──WS──▶ FastAPI ──WS──▶ Agent (Android)
│ │
└──HTTP REST──▶ SQLite (target, command, dump, build)
│
└── apktool / zipalign / apksigner


- Semua trafik operator lewat cookie sesi `HttpOnly`; WS memvalidasi cookie yang sama.
- Agent diidentifikasi oleh token acak per-build (disimpan di meta-data manifest).
- Command punya status `queued → sent → done|error`, jadi target offline tetap menerima perintah saat reconnect.
- Dump masuk lewat WS sebagai base64, ditulis ke `data/dumps/<target>/`, diindeks dengan SHA-256.
- Build berjalan di thread terpisah, log streaming ke tabel `builds`.

Batas keamanan: tidak ada auth multi-user. Satu lisensi = satu instance. Bind ke `127.0.0.1` bila tidak butuh akses LAN.
