param(
  [Parameter(Mandatory = $true)]
  [string]$BackendBaseUrl,
  [string]$UserId = "cloud-smoke-user",
  [int]$ExpiresMinutes = 30,
  [int]$TimeoutSec = 30,
  [switch]$TriggerSnapshot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-HasKeys {
  param(
    [Parameter(Mandatory = $true)]$Object,
    [Parameter(Mandatory = $true)][string[]]$Keys,
    [Parameter(Mandatory = $true)][string]$Context
  )
  foreach ($k in $Keys) {
    if (-not ($Object.PSObject.Properties.Name -contains $k)) {
      throw "$Context missing required field: $k"
    }
  }
}

try {
  $base = $BackendBaseUrl.TrimEnd("/")
  if (-not $base.StartsWith("http")) {
    throw "BackendBaseUrl must start with http/https."
  }

  Write-Host "[1/6] Health check: $base/health"
  $health = Invoke-RestMethod -Method Get -Uri "$base/health" -TimeoutSec $TimeoutSec
  if ($health.status -ne "ok") {
    throw "Health check failed: status=$($health.status)"
  }
  if (-not $health.services.postgres.ok) {
    throw "Health check failed: postgres not ok"
  }
  if (-not $health.services.redis.ok) {
    throw "Health check failed: redis not ok"
  }

  Write-Host "[2/6] Issue JWT token"
  $tokenResp = Invoke-RestMethod -Method Post -Uri "$base/auth/token" -ContentType "application/json" -TimeoutSec $TimeoutSec -Body (@{
      user_id = $UserId
      expires_minutes = $ExpiresMinutes
    } | ConvertTo-Json -Compress)
  Assert-HasKeys -Object $tokenResp -Keys @("access_token") -Context "token response"
  $token = [string]$tokenResp.access_token
  if ([string]::IsNullOrWhiteSpace($token)) {
    throw "token response access_token is empty"
  }

  $headers = @{ Authorization = "Bearer $token" }

  Write-Host "[3/6] Quote checks"
  $q2330 = Invoke-RestMethod -Method Get -Uri "$base/stocks/quote?symbol=2330" -Headers $headers -TimeoutSec $TimeoutSec
  $q00878 = Invoke-RestMethod -Method Get -Uri "$base/stocks/quote?symbol=00878" -Headers $headers -TimeoutSec $TimeoutSec
  Assert-HasKeys -Object $q2330 -Keys @("symbol", "source", "quote_time", "market_state", "is_realtime", "source_priority", "freshness") -Context "quote(2330)"
  Assert-HasKeys -Object $q00878 -Keys @("symbol", "source", "quote_time", "market_state", "is_realtime", "source_priority", "freshness") -Context "quote(00878)"

  Write-Host "[4/6] Movers check"
  $movers = Invoke-RestMethod -Method Get -Uri "$base/stocks/movers?limit=6" -Headers $headers -TimeoutSec $TimeoutSec
  Assert-HasKeys -Object $movers -Keys @("as_of_date", "categories", "coverage_ratio", "requested_trade_date") -Context "movers"
  Assert-HasKeys -Object $movers.categories -Keys @("top_volume", "top_gainers", "top_losers") -Context "movers.categories"

  if ($TriggerSnapshot.IsPresent) {
    Write-Host "[5/6] Snapshot trigger check"
    $snapshot = Invoke-RestMethod -Method Post -Uri "$base/stocks/pipeline/snapshot?max_symbols=3000" -Headers $headers -TimeoutSec $TimeoutSec
    Assert-HasKeys -Object $snapshot -Keys @("ok", "inserted_rows", "trade_date", "coverage_ratio") -Context "snapshot"
  } else {
    Write-Host "[5/6] Snapshot trigger skipped"
  }

  Write-Host "[6/6] Pipeline status check"
  $pipeline = Invoke-RestMethod -Method Get -Uri "$base/stocks/pipeline/status" -Headers $headers -TimeoutSec $TimeoutSec
  Assert-HasKeys -Object $pipeline -Keys @("status", "is_healthy", "latest_trade_date", "coverage_ratio", "note") -Context "pipeline_status"

  $summary = [PSCustomObject]@{
    quote_2330_source    = $q2330.source
    quote_00878_source   = $q00878.source
    movers_date          = $movers.as_of_date
    movers_coverage      = $movers.coverage_ratio
    pipeline_status      = $pipeline.status
    pipeline_trade_date  = $pipeline.latest_trade_date
    pipeline_coverage    = $pipeline.coverage_ratio
  }

  Write-Host ""
  Write-Host "Cloud smoke summary:"
  $summary | Format-List | Out-String | Write-Host
  Write-Host "Cloud smoke check PASSED"
}
catch {
  Write-Error "Cloud smoke check FAILED: $($_.Exception.Message)"
  exit 1
}
