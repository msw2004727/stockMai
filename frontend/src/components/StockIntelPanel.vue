<script setup>
defineProps({
  intelOverview: { type: Object, default: null },
  intelOverviewLoading: { type: Boolean, default: false },
  intelOverviewError: { type: String, default: "" },
  intelDeep: { type: Object, default: null },
  intelDeepLoading: { type: Boolean, default: false },
  intelDeepError: { type: String, default: "" },
  intelStatus: { type: Object, default: null },
  intelStatusError: { type: String, default: "" },
});

function statusText(status) {
  const value = String(status || "").toLowerCase();
  if (value === "ok") return "可用";
  if (value === "restricted") return "權限限制";
  if (value === "error") return "錯誤";
  if (value === "empty") return "暫無資料";
  return "未知";
}

function statusClass(status) {
  const value = String(status || "").toLowerCase();
  if (value === "ok") return "ok";
  if (value === "restricted") return "warn";
  if (value === "error") return "warn";
  return "";
}

function fmtNumber(value, digits = 0) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return "--";
  if (digits > 0) return parsed.toFixed(digits);
  return new Intl.NumberFormat("zh-TW").format(Math.round(parsed));
}

function fmtPct(value) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return "--";
  return `${parsed.toFixed(2)}%`;
}

function hasRows(rows) {
  return Array.isArray(rows) && rows.length > 0;
}
</script>

<template>
  <section class="stock-intel-section">
    <h3 class="section-title">市場資訊擴充</h3>

    <details class="intel-block" open>
      <summary class="intel-summary">籌碼與營收（即時拉取）</summary>
      <p v-if="intelOverviewLoading" class="sub">正在載入籌碼與營收資料...</p>
      <p v-if="intelOverviewError" class="sub warn-text">{{ intelOverviewError }}</p>

      <div v-if="intelOverview" class="intel-grid">
        <article class="card">
          <p class="label">三大法人</p>
          <p class="sub">資料日：{{ intelOverview.institutional_flow?.data_as_of || "--" }}</p>
          <p class="sub">
            狀態：
            <span :class="statusClass(intelOverview.institutional_flow?.availability?.status)">
              {{ statusText(intelOverview.institutional_flow?.availability?.status) }}
            </span>
          </p>
          <div v-if="hasRows(intelOverview.institutional_flow?.rows)" class="intel-table-wrap">
            <table class="intel-table">
              <thead>
                <tr>
                  <th>法人</th>
                  <th>買</th>
                  <th>賣</th>
                  <th>淨額</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in intelOverview.institutional_flow.rows.slice(0, 8)" :key="`${row.investor}-${row.net}`">
                  <td>{{ row.investor || "--" }}</td>
                  <td>{{ fmtNumber(row.buy) }}</td>
                  <td>{{ fmtNumber(row.sell) }}</td>
                  <td>{{ fmtNumber(row.net) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="sub">暫無三大法人資料。</p>
        </article>

        <article class="card">
          <p class="label">融資融券</p>
          <p class="sub">資料日：{{ intelOverview.margin_short?.data_as_of || "--" }}</p>
          <p class="sub">融資餘額：{{ fmtNumber(intelOverview.margin_short?.summary?.margin_purchase_balance) }}</p>
          <p class="sub">融券餘額：{{ fmtNumber(intelOverview.margin_short?.summary?.short_sale_balance) }}</p>
          <p class="sub">融資增減：{{ fmtNumber(intelOverview.margin_short?.summary?.margin_purchase_change) }}</p>
          <p class="sub">融券增減：{{ fmtNumber(intelOverview.margin_short?.summary?.short_sale_change) }}</p>
        </article>

        <article class="card">
          <p class="label">外資持股</p>
          <p class="sub">資料日：{{ intelOverview.foreign_holding?.data_as_of || "--" }}</p>
          <p class="sub">持股比率：{{ fmtPct(intelOverview.foreign_holding?.summary?.holding_ratio_pct) }}</p>
          <p class="sub">持股股數：{{ fmtNumber(intelOverview.foreign_holding?.summary?.holding_shares) }}</p>
        </article>

        <article class="card">
          <p class="label">月營收</p>
          <p class="sub">最新月份：{{ intelOverview.monthly_revenue?.summary?.latest_month || "--" }}</p>
          <p class="sub">當月營收：{{ fmtNumber(intelOverview.monthly_revenue?.summary?.latest_revenue) }}</p>
          <p class="sub">MoM：{{ fmtPct(intelOverview.monthly_revenue?.summary?.latest_mom_pct) }}</p>
          <p class="sub">YoY：{{ fmtPct(intelOverview.monthly_revenue?.summary?.latest_yoy_pct) }}</p>
        </article>
      </div>
    </details>

    <details class="intel-block">
      <summary class="intel-summary">深度籌碼與財報</summary>
      <p v-if="intelDeepLoading" class="sub">正在載入深度資料...</p>
      <p v-if="intelDeepError" class="sub warn-text">{{ intelDeepError }}</p>

      <div v-if="intelDeep" class="intel-grid">
        <article class="card">
          <p class="label">股權分散</p>
          <p class="sub">資料日：{{ intelDeep.shareholding_distribution?.data_as_of || "--" }}</p>
          <div v-if="hasRows(intelDeep.shareholding_distribution?.rows)" class="intel-table-wrap">
            <table class="intel-table">
              <thead>
                <tr>
                  <th>級距</th>
                  <th>人數</th>
                  <th>占比</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in intelDeep.shareholding_distribution.rows.slice(0, 10)" :key="`${row.level}-${row.ratio_pct}`">
                  <td>{{ row.level || "--" }}</td>
                  <td>{{ fmtNumber(row.people) }}</td>
                  <td>{{ fmtPct(row.ratio_pct) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="sub">暫無股權分散資料。</p>
        </article>

        <article class="card">
          <p class="label">借券</p>
          <p class="sub">資料日：{{ intelDeep.securities_lending?.data_as_of || "--" }}</p>
          <p class="sub">借券餘額：{{ fmtNumber(intelDeep.securities_lending?.summary?.lending_balance) }}</p>
          <p class="sub">借券賣出：{{ fmtNumber(intelDeep.securities_lending?.summary?.lending_sell) }}</p>
          <p class="sub">借券還券：{{ fmtNumber(intelDeep.securities_lending?.summary?.lending_return) }}</p>
        </article>

        <article class="card">
          <p class="label">券商分點</p>
          <p class="sub">資料日：{{ intelDeep.broker_branches?.data_as_of || "--" }}</p>
          <p class="sub">
            狀態：
            <span :class="statusClass(intelDeep.broker_branches?.availability?.status)">
              {{ statusText(intelDeep.broker_branches?.availability?.status) }}
            </span>
          </p>
          <div v-if="hasRows(intelDeep.broker_branches?.rows)" class="intel-table-wrap">
            <table class="intel-table">
              <thead>
                <tr>
                  <th>分點</th>
                  <th>買</th>
                  <th>賣</th>
                  <th>淨額</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in intelDeep.broker_branches.rows.slice(0, 8)" :key="`${row.broker}-${row.net}`">
                  <td>{{ row.broker || "--" }}</td>
                  <td>{{ fmtNumber(row.buy) }}</td>
                  <td>{{ fmtNumber(row.sell) }}</td>
                  <td>{{ fmtNumber(row.net) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="sub">暫無券商分點資料，可能需要更高權限。</p>
        </article>

        <article class="card full-span">
          <p class="label">財報摘要</p>
          <p class="sub">資料日：{{ intelDeep.financial_statements?.data_as_of || "--" }}</p>
          <div v-if="hasRows(intelDeep.financial_statements?.sections)" class="financial-sections">
            <details
              v-for="section in intelDeep.financial_statements.sections"
              :key="`${section.kind}-${section.data_as_of}`"
              class="financial-section-card"
            >
              <summary>{{ section.kind }}（{{ statusText(section.availability?.status) }}）</summary>
              <div v-if="hasRows(section.rows)" class="intel-table-wrap">
                <table class="intel-table">
                  <thead>
                    <tr>
                      <th>科目</th>
                      <th>數值</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in section.rows.slice(0, 10)" :key="`${row.subject}-${row.value}`">
                      <td>{{ row.subject || "--" }}</td>
                      <td>{{ fmtNumber(row.value) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p v-else class="sub">此區塊目前無資料。</p>
            </details>
          </div>
          <p v-else class="sub">暫無財報資料。</p>
        </article>
      </div>
    </details>

    <details class="intel-block">
      <summary class="intel-summary">資料可用性與來源</summary>
      <p v-if="intelStatusError" class="sub warn-text">{{ intelStatusError }}</p>
      <p v-if="intelStatus?.fetched_at" class="sub">抓取時間：{{ intelStatus.fetched_at }}</p>
      <div v-if="intelStatus?.datasets" class="intel-table-wrap">
        <table class="intel-table">
          <thead>
            <tr>
              <th>資料集</th>
              <th>狀態</th>
              <th>資料日</th>
              <th>訊息</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(value, key) in intelStatus.datasets" :key="key">
              <td>{{ key }}</td>
              <td :class="statusClass(value?.status)">{{ statusText(value?.status) }}</td>
              <td>{{ value?.data_as_of || "--" }}</td>
              <td>{{ value?.message || "--" }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="sub">尚未取得可用性資訊。</p>
    </details>
  </section>
</template>
