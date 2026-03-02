param(
  [Parameter(Mandatory = $true)]
  [string]$BackendBaseUrl,
  [string]$UserId = "cloud-smoke-user",
  [int]$ExpiresMinutes = 30,
  [int]$TimeoutSec = 30
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

  Write-Host "[1/4] Health check: $base/health"
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

  Write-Host "[2/4] Issue JWT token"
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

  Write-Host "[3/4] Quote check: symbol=2330"
  $q2330 = Invoke-RestMethod -Method Get -Uri "$base/stocks/quote?symbol=2330" -Headers $headers -TimeoutSec $TimeoutSec
  Assert-HasKeys -Object $q2330 -Keys @("symbol", "source", "quote_time", "market_state", "is_realtime", "source_priority", "freshness") -Context "quote(2330)"
  Assert-HasKeys -Object $q2330.freshness -Keys @("as_of_date", "age_days", "is_fresh", "max_age_days") -Context "quote(2330).freshness"

  Write-Host "[4/4] Quote check: symbol=00878"
  $q00878 = Invoke-RestMethod -Method Get -Uri "$base/stocks/quote?symbol=00878" -Headers $headers -TimeoutSec $TimeoutSec
  Assert-HasKeys -Object $q00878 -Keys @("symbol", "source", "quote_time", "market_state", "is_realtime", "source_priority", "freshness") -Context "quote(00878)"
  Assert-HasKeys -Object $q00878.freshness -Keys @("as_of_date", "age_days", "is_fresh", "max_age_days") -Context "quote(00878).freshness"

  $summary = @(
    [PSCustomObject]@{
      symbol          = $q2330.symbol
      source          = $q2330.source
      is_realtime     = $q2330.is_realtime
      source_priority = $q2330.source_priority
      quote_time      = $q2330.quote_time
      cache_hit       = $q2330.cache_hit
    },
    [PSCustomObject]@{
      symbol          = $q00878.symbol
      source          = $q00878.source
      is_realtime     = $q00878.is_realtime
      source_priority = $q00878.source_priority
      quote_time      = $q00878.quote_time
      cache_hit       = $q00878.cache_hit
    }
  )

  Write-Host ""
  Write-Host "Cloud smoke summary:"
  $summary | Format-Table -AutoSize | Out-String | Write-Host
  Write-Host "Cloud smoke check PASSED"
}
catch {
  Write-Error "Cloud smoke check FAILED: $($_.Exception.Message)"
  exit 1
}
