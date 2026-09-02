Write-Host "=== Levantando infraestructura resiliente ===" -ForegroundColor Cyan
docker compose up -d --build

Start-Sleep -Seconds 2

Write-Host "`n=== 1. Test Seguridad: Acceso sin Token (Debe fallar 401) ===" -ForegroundColor Yellow
try {
    $res1 = Invoke-WebRequest -Uri "http://localhost/process" -Method POST -ErrorAction Stop
    Write-Host "Status: $($res1.StatusCode)"
} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Green
}

Write-Host "`n=== 2. Test Seguridad: Payload Malformado con item_id: -5 (Debe fallar 422) ===" -ForegroundColor Yellow
try {
    $headers = @{
        "Authorization" = "Bearer TFU-UT2-SECRET-KEY"
        "Content-Type" = "application/json"
    }
    $body = '{"item_id": -5, "name": "Test"}'
    $res2 = Invoke-WebRequest -Uri "http://localhost/process" -Method POST -Headers $headers -Body $body -ErrorAction Stop
    Write-Host "Status: $($res2.StatusCode)"
} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Green
}

Write-Host "`n=== 3. Test Disponibilidad: Ejecutando carga concurrente y deteniendo replica... ===" -ForegroundColor Yellow
$job = Start-Job -ScriptBlock {
    param($path)
    python "$path\client_test.py"
} -ArgumentList (Get-Location).Path

Start-Sleep -Seconds 2

Write-Host "`nDeteniendo nodo 'web_replica_1' en caliente..." -ForegroundColor Red
docker stop web_replica_1
Write-Host "Nodo 'web_replica_1' detenido. Observe como los re-intentos mitigan la transicion." -ForegroundColor Green

$output = Receive-Job -Job $job -Wait
Write-Host "`n--- Resultado de la Carga Concurrente ---" -ForegroundColor Cyan
$output
Remove-Job -Job $job
