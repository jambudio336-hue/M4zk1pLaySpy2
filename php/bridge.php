<?php
// Reverse-proxy tipis ke C2 lokal (opsional).
$target = getenv('MZK_C2') ?: 'http://127.0.0.1:8777';
$path = $_SERVER['REQUEST_URI'] ?? '/';
$url = rtrim($target, '/') . $path;

$ch = curl_init($url);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HEADER => true,
    CURLOPT_CUSTOMREQUEST => $_SERVER['REQUEST_METHOD'],
    CURLOPT_FOLLOWLOCATION => false,
    CURLOPT_TIMEOUT => 30,
]);
$raw = curl_exec($ch);
if ($raw === false) {
    http_response_code(502);
    echo 'bridge gagal: ' . curl_error($ch);
    exit;
}
$hsize = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
$headers = substr($raw, 0, $hsize);
$body = substr($raw, $hsize);
foreach (explode("\r\n", $headers) as $line) {
    if (stripos($line, 'HTTP/') === 0) continue;
    if (trim($line) === '') continue;
    header($line, false);
}
echo $body;
curl_close($ch);
