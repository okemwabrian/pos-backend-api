$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "portable-pos"))
$rootPrefix = $root.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
$address = [System.Net.IPAddress]::Loopback
$listener = New-Object System.Net.Sockets.TcpListener($address, 8766)

function Get-ContentType($path) {
    switch ([System.IO.Path]::GetExtension($path).ToLowerInvariant()) {
        ".html" { return "text/html; charset=utf-8" }
        ".js" { return "application/javascript; charset=utf-8" }
        ".css" { return "text/css; charset=utf-8" }
        ".svg" { return "image/svg+xml" }
        ".webmanifest" { return "application/manifest+json" }
        ".json" { return "application/json; charset=utf-8" }
        ".png" { return "image/png" }
        ".jpg" { return "image/jpeg" }
        ".jpeg" { return "image/jpeg" }
        ".woff" { return "font/woff" }
        ".woff2" { return "font/woff2" }
        ".ico" { return "image/x-icon" }
        default { return "application/octet-stream" }
    }
}

$url = "http://127.0.0.1:8766/"
$chromeCandidates = @(
    (Join-Path $env:ProgramFiles "Google\Chrome\Application\chrome.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Google\Chrome\Application\chrome.exe"),
    (Join-Path $env:LOCALAPPDATA "Google\Chrome\Application\chrome.exe")
)
$chrome = $chromeCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

try {
    $listener.Start()
    if ($chrome) {
        $profile = Join-Path $env:LOCALAPPDATA "ChiwasPOS\BrowserProfile"
        New-Item -ItemType Directory -Force -Path $profile | Out-Null
        $arguments = "--app=`"$url`" --user-data-dir=`"$profile`" --no-first-run"
        Start-Process -FilePath $chrome -ArgumentList $arguments
    } else {
        Write-Host "Install a Chromium-based browser (Chrome 109 or newer) to use FREE HOUSE POS."
        Start-Process $url
    }
    Write-Host "FREE HOUSE BAR & RESTAURANT POS is running locally at $url. Close this window to stop it."
    Write-Host "The app and its IndexedDB data stay on this computer; no Python is needed."

    while ($listener.Server.IsBound) {
        $client = $listener.AcceptTcpClient()
        try {
            $stream = $client.GetStream()
            $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::ASCII)
            $requestLine = $reader.ReadLine()
            while ($reader.ReadLine() -ne "") { }
            $segments = $requestLine.Split(" ")
            $requestPath = [System.Uri]::UnescapeDataString(($segments[1] -split "\?")[0]).TrimStart("/")
            if ([string]::IsNullOrEmpty($requestPath)) { $requestPath = "index.html" }
            $filePath = [System.IO.Path]::GetFullPath((Join-Path $root ($requestPath -replace "/", "\")))

            if (-not $filePath.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or -not (Test-Path -LiteralPath $filePath -PathType Leaf)) {
                $status = "404 Not Found"
                $body = [System.Text.Encoding]::UTF8.GetBytes("Not found")
                $contentType = "text/plain; charset=utf-8"
            } else {
                $status = "200 OK"
                $body = [System.IO.File]::ReadAllBytes($filePath)
                $contentType = Get-ContentType $filePath
            }

            $headers = "HTTP/1.1 $status`r`nContent-Type: $contentType`r`nContent-Length: $($body.Length)`r`nCache-Control: no-cache`r`nConnection: close`r`n`r`n"
            $headerBytes = [System.Text.Encoding]::ASCII.GetBytes($headers)
            $stream.Write($headerBytes, 0, $headerBytes.Length)
            $stream.Write($body, 0, $body.Length)
            $stream.Flush()
        } catch {
            Write-Warning "A local POS request failed: $($_.Exception.Message)"
        } finally {
            if ($reader) { $reader.Close() }
            $client.Close()
        }
    }
} finally {
    $listener.Stop()
}
