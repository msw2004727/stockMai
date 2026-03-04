<script setup>
import { computed, toRefs } from "vue";

const props = defineProps({
  intelOverview: { type: Object, default: null },
  intelOverviewLoading: { type: Boolean, default: false },
  intelOverviewError: { type: String, default: "" },
  intelDeep: { type: Object, default: null },
  intelDeepLoading: { type: Boolean, default: false },
  intelDeepError: { type: String, default: "" },
  intelStatus: { type: Object, default: null },
  intelStatusError: { type: String, default: "" },
});

const {
  intelOverview,
  intelOverviewLoading,
  intelOverviewError,
  intelDeep,
  intelDeepLoading,
  intelDeepError,
  intelStatus,
  intelStatusError,
} = toRefs(props);

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

function fmtSignedPct(value) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return "--";
  const sign = parsed > 0 ? "+" : "";
  return `${sign}${parsed.toFixed(2)}%`;
}

function freshnessLabel(freshness) {
  const level = String(freshness?.level || "").toLowerCase();
  if (level === "fresh") return "新鮮";
  if (level === "watch") return "稍延遲";
  if (level === "stale") return "過舊";
  return "未知";
}

function freshnessClass(freshness) {
  const level = String(freshness?.level || "").toLowerCase();
  if (level === "fresh") return "freshness-ok";
  if (level === "watch") return "freshness-watch";
  if (level === "stale") return "freshness-stale";
  return "freshness-unknown";
}

function freshnessHint(block) {
  const cadence = String(block?.freshness?.cadence_label || "--");
  const days = Number(block?.freshness?.staleness_days);
  if (Number.isFinite(days)) {
    return `${cadence}・延遲 ${days} 天`;
  }
  return `${cadence}・延遲未知`;
}

function hasRows(rows) {
  return Array.isArray(rows) && rows.length > 0;
}

function investorLabel(rawInvestor) {
  const raw = String(rawInvestor || "").trim();
  if (!raw) return "--";

  const normalized = raw.toLowerCase().replace(/\s+/g, "_");
  if (
    normalized.includes("foreign") ||
    normalized.includes("foreign_investor") ||
    raw.includes("外資")
  ) {
    return "外資";
  }
  if (
    normalized.includes("investment_trust") ||
    normalized === "trust" ||
    raw.includes("投信")
  ) {
    return "投信";
  }
  if (
    normalized.includes("dealer") ||
    raw.includes("自營")
  ) {
    return "自營商";
  }

  return raw;
}

function statusRank(status) {
  const value = String(status || "").toLowerCase();
  if (value === "ok") return 0;
  if (value === "restricted") return 1;
  if (value === "empty") return 2;
  if (value === "error") return 3;
  return 4;
}

function freshnessRank(freshness) {
  const level = String(freshness?.level || "").toLowerCase();
  if (level === "fresh") return 0;
  if (level === "watch") return 1;
  if (level === "stale") return 2;
  return 3;
}

function blockPriority(block) {
  if (!block || typeof block !== "object") return 999;
  const s = statusRank(block?.availability?.status ?? block?.status);
  const f = freshnessRank(block?.freshness);
  return f * 10 + s;
}

function cardOrder(block, base = 0) {
  return blockPriority(block) * 10 + Number(base || 0);
}

function sectionBestPriority(blocks) {
  if (!Array.isArray(blocks) || blocks.length === 0) return 999;
  let minRank = 999;
  for (const block of blocks) {
    const rank = blockPriority(block);
    if (rank < minRank) {
      minRank = rank;
    }
  }
  return minRank;
}

const overviewBlocks = computed(() => [
  intelOverview.value?.company_profile,
  intelOverview.value?.valuation,
  intelOverview.value?.institutional_flow,
  intelOverview.value?.margin_short,
  intelOverview.value?.foreign_holding,
  intelOverview.value?.monthly_revenue,
].filter((item) => item && typeof item === "object"));

const deepBlocks = computed(() => [
  intelDeep.value?.price_performance,
  intelDeep.value?.shareholding_distribution,
  intelDeep.value?.securities_lending,
  intelDeep.value?.broker_branches,
  intelDeep.value?.financial_statements,
].filter((item) => item && typeof item === "object"));

const overviewBestPriority = computed(() => sectionBestPriority(overviewBlocks.value));
const deepBestPriority = computed(() => sectionBestPriority(deepBlocks.value));

const shouldOpenOverview = computed(() => {
  if (!intelOverview.value) return true;
  if (!intelDeep.value) return true;
  return overviewBestPriority.value <= deepBestPriority.value;
});

const shouldOpenDeep = computed(() => {
  if (!intelDeep.value) return false;
  return deepBestPriority.value < overviewBestPriority.value;
});

const sortedStatusRows = computed(() => {
  const datasets = intelStatus.value?.datasets;
  if (!datasets || typeof datasets !== "object") return [];
  return Object.entries(datasets)
    .map(([key, value]) => ({ key, value: value && typeof value === "object" ? value : {} }))
    .sort((a, b) => {
      const rankA = blockPriority(a.value);
      const rankB = blockPriority(b.value);
      if (rankA !== rankB) return rankA - rankB;
      const staleA = Number(a.value?.freshness?.staleness_days);
      const staleB = Number(b.value?.freshness?.staleness_days);
      if (Number.isFinite(staleA) && Number.isFinite(staleB) && staleA !== staleB) {
        return staleA - staleB;
      }
      return String(a.key).localeCompare(String(b.key), "zh-Hant");
    });
});

const shouldOpenStatus = computed(() => {
  const rows = sortedStatusRows.value;
  if (!rows.length) return false;
  return rows.some((entry) => {
    const currentStatus = String(entry.value?.status || "").toLowerCase();
    const currentFresh = String(entry.value?.freshness?.level || "").toLowerCase();
    return currentStatus !== "ok" || currentFresh === "watch" || currentFresh === "stale" || currentFresh === "unknown";
  });
});
</script>

<template>
  <section class="stock-intel-section">
    <h3 class="section-title">市場資訊擴充</h3>

    <details class="intel-block" :open="shouldOpenOverview">
      <summary class="intel-summary">籌碼與營收（即時拉取）</summary>
      <p v-if="intelOverviewLoading" class="sub">正在載入籌碼與營收資料...</p>
      <p v-if="intelOverviewError" class="sub warn-text">{{ intelOverviewError }}</p>

      <div v-if="intelOverview" class="intel-grid">
        <article class="card" :style="{ order: cardOrder(intelOverview.company_profile, 1) }">
          <p class="label">公司基本資料</p>
          <p class="sub">代號：{{ intelOverview.company_profile?.summary?.stock_id || "--" }}</p>
          <p class="sub">簡稱：{{ intelOverview.company_profile?.summary?.stock_name || "--" }}</p>
          <p class="sub">產業：{{ intelOverview.company_profile?.summary?.industry || "--" }}</p>
          <p class="sub">市場：{{ intelOverview.company_profile?.summary?.market || "--" }}</p>
          <p class="sub">類型：{{ intelOverview.company_profile?.summary?.listing_type || "--" }}</p>
          <p class="sub">更新：{{ freshnessHint(intelOverview.company_profile) }}</p>
          <p class="sub">
            新鮮度：
            <span :class="freshnessClass(intelOverview.company_profile?.freshness)">
              {{ freshnessLabel(intelOverview.company_profile?.freshness) }}
            </span>
          </p>
        </article>

        <article class="card" :style="{ order: cardOrder(intelOverview.valuation, 2) }">
          <p class="label">估值指標</p>
          <p class="sub">資料日：{{ intelOverview.valuation?.data_as_of || "--" }}</p>
          <p class="sub">本益比 (PER)：{{ fmtNumber(intelOverview.valuation?.summary?.latest_per, 2) }}</p>
          <p class="sub">股價淨值比 (PBR)：{{ fmtNumber(intelOverview.valuation?.summary?.latest_pbr, 2) }}</p>
          <p class="sub">殖利率：{{ fmtPct(intelOverview.valuation?.summary?.latest_dividend_yield_pct) }}</p>
          <p class="sub">更新：{{ freshnessHint(intelOverview.valuation) }}</p>
          <p class="sub">
            新鮮度：
            <span :class="freshnessClass(intelOverview.valuation?.freshness)">
              {{ freshnessLabel(intelOverview.valuation?.freshness) }}
            </span>
          </p>
        </article>

        <article class="card" :style="{ order: cardOrder(intelOverview.institutional_flow, 3) }">
          <p class="label">三大法人</p>
          <p class="sub">資料日：{{ intelOverview.institutional_flow?.data_as_of || "--" }}</p>
          <p class="sub">更新：{{ freshnessHint(intelOverview.institutional_flow) }}</p>
          <p class="sub">
            新鮮度：
            <span :class="freshnessClass(intelOverview.institutional_flow?.freshness)">
              {{ freshnessLabel(intelOverview.institutional_flow?.freshness) }}
            </span>
          </p>
          <p class="sub">
            狀態：
            <span :class="statusClass(intelOverview.institutional_flow?.availability?.status)">
              {{ statusText(intelOverview.institutional_flow?.availability?.status) }}
            </span>
          </p>
          <div
            v-if="hasRows(intelOverview.institutional_flow?.rows)"
            class="intel-table-wrap intel-table-wrap-mobile-scroll"
          >
            <table class="intel-table intel-table-institutional">
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
                  <td>{{ investorLabel(row.investor) }}</td>
                  <td>{{ fmtNumber(row.buy) }}</td>
                  <td>{{ fmtNumber(row.sell) }}</td>
                  <td>{{ fmtNumber(row.net) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="sub">暫無三大法人資料。</p>
        </article>

        <article class="card" :style="{ order: cardOrder(intelOverview.margin_short, 4) }">
          <p class="label">融資融券</p>
          <p class="sub">資料日：{{ intelOverview.margin_short?.data_as_of || "--" }}</p>
          <p class="sub">更新：{{ freshnessHint(intelOverview.margin_short) }}</p>
          <p class="sub">
            新鮮度：
            <span :class="freshnessClass(intelOverview.margin_short?.freshness)">
              {{ freshnessLabel(intelOverview.margin_short?.freshness) }}
            </span>
          </p>
          <p class="sub">融資餘額：{{ fmtNumber(intelOverview.margin_short?.summary?.margin_purchase_balance) }}</p>
          <p class="sub">融券餘額：{{ fmtNumber(intelOverview.margin_short?.summary?.short_sale_balance) }}</p>
          <p class="sub">融資增減：{{ fmtNumber(intelOverview.margin_short?.summary?.margin_purchase_change) }}</p>
          <p class="sub">融券增減：{{ fmtNumber(intelOverview.margin_short?.summary?.short_sale_change) }}</p>
        </article>

        <article class="card" :style="{ order: cardOrder(intelOverview.foreign_holding, 5) }">
          <p class="label">外資持股</p>
          <p class="sub">資料日：{{ intelOverview.foreign_holding?.data_as_of || "--" }}</p>
          <p class="sub">更新：{{ freshnessHint(intelOverview.foreign_holding) }}</p>
          <p class="sub">
            新鮮度：
            <span :class="freshnessClass(intelOverview.foreign_holding?.freshness)">
              {{ freshnessLabel(intelOverview.foreign_holding?.freshness) }}
            </span>
          </p>
          <p class="sub">持股比率：{{ fmtPct(intelOverview.foreign_holding?.summary?.holding_ratio_pct) }}</p>
          <p class="sub">持股股數：{{ fmtNumber(intelOverview.foreign_holding?.summary?.holding_shares) }}</p>
        </article>

        <article class="card" :style="{ order: cardOrder(intelOverview.monthly_revenue, 6) }">
          <p class="label">月營收</p>
          <p class="sub">最新月份：{{ intelOverview.monthly_revenue?.summary?.latest_month || "--" }}</p>
          <p class="sub">更新：{{ freshnessHint(intelOverview.monthly_revenue) }}</p>
          <p class="sub">
            新鮮度：
            <span :class="freshnessClass(intelOverview.monthly_revenue?.freshness)">
              {{ freshnessLabel(intelOverview.monthly_revenue?.freshness) }}
            </span>
          </p>
          <p class="sub">當月營收：{{ fmtNumber(intelOverview.monthly_revenue?.summary?.latest_revenue) }}</p>
          <p class="sub">MoM：{{ fmtPct(intelOverview.monthly_revenue?.summary?.latest_mom_pct) }}</p>
          <p class="sub">YoY：{{ fmtPct(intelOverview.monthly_revenue?.summary?.latest_yoy_pct) }}</p>
        </article>
      </div>
    </details>

    <details class="intel-block" :open="shouldOpenDeep">
      <summary class="intel-summary">深度籌碼與財報</summary>
      <p v-if="intelDeepLoading" class="sub">正在載入深度資料...</p>
      <p v-if="intelDeepError" class="sub warn-text">{{ intelDeepError }}</p>

      <div v-if="intelDeep" class="intel-grid">
        <article class="card" :style="{ order: cardOrder(intelDeep.price_performance, 1) }">
          <p class="label">股價績效</p>
          <p class="sub">資料日：{{ intelDeep.price_performance?.data_as_of || "--" }}</p>
          <p class="sub">更新：{{ freshnessHint(intelDeep.price_performance) }}</p>
          <p class="sub">
            新鮮度：
            <span :class="freshnessClass(intelDeep.price_performance?.freshness)">
              {{ freshnessLabel(intelDeep.price_performance?.freshness) }}
            </span>
          </p>
          <p class="sub">近 1 月：{{ fmtSignedPct(intelDeep.price_performance?.summary?.return_1m_pct) }}</p>
          <p class="sub">近 3 月：{{ fmtSignedPct(intelDeep.price_performance?.summary?.return_3m_pct) }}</p>
          <p class="sub">近 1 年：{{ fmtSignedPct(intelDeep.price_performance?.summary?.return_1y_pct) }}</p>
          <p class="sub">52 週高點：{{ fmtNumber(intelDeep.price_performance?.summary?.high_52w, 2) }}</p>
          <p class="sub">52 週低點：{{ fmtNumber(intelDeep.price_performance?.summary?.low_52w, 2) }}</p>
        </article>

        <article class="card" :style="{ order: cardOrder(intelDeep.shareholding_distribution, 2) }">
          <p class="label">股權分散</p>
          <p class="sub">資料日：{{ intelDeep.shareholding_distribution?.data_as_of || "--" }}</p>
          <p class="sub">更新：{{ freshnessHint(intelDeep.shareholding_distribution) }}</p>
          <p class="sub">
            新鮮度：
            <span :class="freshnessClass(intelDeep.shareholding_distribution?.freshness)">
              {{ freshnessLabel(intelDeep.shareholding_distribution?.freshness) }}
            </span>
          </p>
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

        <article class="card" :style="{ order: cardOrder(intelDeep.securities_lending, 3) }">
          <p class="label">借券</p>
          <p class="sub">資料日：{{ intelDeep.securities_lending?.data_as_of || "--" }}</p>
          <p class="sub">更新：{{ freshnessHint(intelDeep.securities_lending) }}</p>
          <p class="sub">
            新鮮度：
            <span :class="freshnessClass(intelDeep.securities_lending?.freshness)">
              {{ freshnessLabel(intelDeep.securities_lending?.freshness) }}
            </span>
          </p>
          <p class="sub">借券餘額：{{ fmtNumber(intelDeep.securities_lending?.summary?.lending_balance) }}</p>
          <p class="sub">借券賣出：{{ fmtNumber(intelDeep.securities_lending?.summary?.lending_sell) }}</p>
          <p class="sub">借券還券：{{ fmtNumber(intelDeep.securities_lending?.summary?.lending_return) }}</p>
        </article>

        <article class="card" :style="{ order: cardOrder(intelDeep.broker_branches, 4) }">
          <p class="label">券商分點</p>
          <p class="sub">資料日：{{ intelDeep.broker_branches?.data_as_of || "--" }}</p>
          <p class="sub">更新：{{ freshnessHint(intelDeep.broker_branches) }}</p>
          <p class="sub">
            新鮮度：
            <span :class="freshnessClass(intelDeep.broker_branches?.freshness)">
              {{ freshnessLabel(intelDeep.broker_branches?.freshness) }}
            </span>
          </p>
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

        <article class="card full-span" :style="{ order: cardOrder(intelDeep.financial_statements, 5) }">
          <p class="label">財報摘要</p>
          <p class="sub">資料日：{{ intelDeep.financial_statements?.data_as_of || "--" }}</p>
          <p class="sub">更新：{{ freshnessHint(intelDeep.financial_statements) }}</p>
          <p class="sub">
            新鮮度：
            <span :class="freshnessClass(intelDeep.financial_statements?.freshness)">
              {{ freshnessLabel(intelDeep.financial_statements?.freshness) }}
            </span>
          </p>
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

    <details class="intel-block" :open="shouldOpenStatus">
      <summary class="intel-summary">資料可用性與來源</summary>
      <p v-if="intelStatusError" class="sub warn-text">{{ intelStatusError }}</p>
      <p v-if="intelStatus?.fetched_at" class="sub">抓取時間：{{ intelStatus.fetched_at }}</p>
      <div v-if="intelStatus?.datasets" class="intel-table-wrap">
        <table class="intel-table">
          <thead>
            <tr>
              <th>資料集</th>
              <th>狀態</th>
              <th>更新節奏</th>
              <th>新鮮度</th>
              <th>資料日</th>
              <th>訊息</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in sortedStatusRows" :key="entry.key">
              <td>{{ entry.key }}</td>
              <td :class="statusClass(entry.value?.status)">{{ statusText(entry.value?.status) }}</td>
              <td>{{ entry.value?.freshness?.cadence_label || "--" }}</td>
              <td :class="freshnessClass(entry.value?.freshness)">{{ freshnessLabel(entry.value?.freshness) }}</td>
              <td>{{ entry.value?.data_as_of || "--" }}</td>
              <td>{{ entry.value?.message || "--" }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="sub">尚未取得可用性資訊。</p>
    </details>
  </section>
</template>
