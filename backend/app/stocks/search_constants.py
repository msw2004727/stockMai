OPEN_DATA_SOURCES = [
    {
        "market": "twse",
        "source": "twse_openapi",
        "url": "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
    }
]

SEARCH_CACHE_TTL_SECONDS = 6 * 60 * 60

FALLBACK_STOCK_UNIVERSE = [
    {"symbol": "2330", "name": "台積電", "market": "twse", "source": "fallback"},
    {"symbol": "2317", "name": "鴻海", "market": "twse", "source": "fallback"},
    {"symbol": "2454", "name": "聯發科", "market": "twse", "source": "fallback"},
    {"symbol": "2308", "name": "台達電", "market": "twse", "source": "fallback"},
    {"symbol": "2382", "name": "廣達", "market": "twse", "source": "fallback"},
    {"symbol": "2882", "name": "國泰金", "market": "twse", "source": "fallback"},
    {"symbol": "2881", "name": "富邦金", "market": "twse", "source": "fallback"},
    {"symbol": "2891", "name": "中信金", "market": "twse", "source": "fallback"},
    {"symbol": "2412", "name": "中華電", "market": "twse", "source": "fallback"},
    {"symbol": "2603", "name": "長榮", "market": "twse", "source": "fallback"},
    {"symbol": "0050", "name": "元大台灣50", "market": "twse", "source": "fallback"},
    {"symbol": "0056", "name": "元大高股息", "market": "twse", "source": "fallback"},
    {"symbol": "00878", "name": "國泰永續高股息", "market": "twse", "source": "fallback"},
    {"symbol": "00919", "name": "群益台灣精選高息", "market": "twse", "source": "fallback"},
]
