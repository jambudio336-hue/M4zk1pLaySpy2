<?php
// Landing ringan untuk deployment shared-hosting.
$c2 = getenv('MZK_C2') ?: 'http://127.0.0.1:8777';
?>
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>M4zk1pLaySpy</title>
<style>
  body{margin:0;min-height:100vh;display:grid;place-items:center;background:#05060a;color:#d6dbe6;
       font-family:ui-monospace,monospace;text-align:center;padding:24px}
  h1{color:#ff2d55;letter-spacing:.28em;font-size:19px}
  p{color:#6b7488;font-size:12px;max-width:420px;line-height:1.7}
  a{margin-top:20px;display:inline-block;background:#ff2d55;color:#fff;padding:12px 22px;
    border-radius:10px;text-decoration:none;font-weight:700;letter-spacing:.14em;font-size:11px}
</style>
</head>
<body>
<div>
  <h1>M4ZK1PL4YSPY</h1>
  <p>C2 fullstack · builder APK · injector RAT. Jalankan server Python lalu masuk dengan lisensi.</p>
  <a href="<?= htmlspecialchars($c2) ?>">BUKA KONSOL</a>
</div>
</body>
</html>
