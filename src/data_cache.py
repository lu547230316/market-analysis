"""统一数据缓存层 — 避免重复API调用 v4.0"""
import akshare as ak


class DataCache:
    """缓存所有 API 调用结果，确保每只股票/指数只查询一次"""

    def __init__(self):
        self._indices = {}  # {symbol: DataFrame}
        self._stocks = {}   # {symbol: DataFrame}
        self._valuations = {}  # {symbol: DataFrame}
        self._news = None
        self._fetched_stocks = set()
        self._fetched_indices = set()
        self._api_calls = 0

    @property
    def api_calls(self):
        return self._api_calls

    def get_index(self, symbol: str) -> "pd.DataFrame":
        """获取指数历史（缓存）"""
        if symbol not in self._fetched_indices:
            try:
                df = ak.index_us_stock_sina(symbol=symbol)
                self._indices[symbol] = df
                self._api_calls += 1
            except Exception:
                self._indices[symbol] = None
            self._fetched_indices.add(symbol)
        return self._indices.get(symbol)

    def get_stock(self, symbol: str) -> "pd.DataFrame":
        """获取个股历史（缓存）"""
        if symbol not in self._fetched_stocks:
            try:
                df = ak.stock_us_daily(symbol=symbol)
                self._stocks[symbol] = df
                self._api_calls += 1
            except Exception:
                self._stocks[symbol] = None
            self._fetched_stocks.add(symbol)
        return self._stocks.get(symbol)

    def get_valuation(self, symbol: str) -> "pd.DataFrame":
        """获取估值（缓存）"""
        if symbol not in self._valuations:
            try:
                df = ak.stock_us_valuation_baidu(symbol=symbol)
                self._valuations[symbol] = df
                self._api_calls += 1
            except Exception:
                self._valuations[symbol] = None
        return self._valuations.get(symbol)

    def get_all_news(self):
        """获取全球财经新闻（缓存）"""
        if self._news is None:
            try:
                self._news = ak.stock_info_global_em()
                self._api_calls += 1
            except Exception:
                self._news = None
        return self._news

    def prefetch_all(self, stock_list: list, index_list: list):
        """预取所有数据，一次性加载"""
        import concurrent.futures
        all_symbols = set(stock_list)
        all_indices = set(index_list)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for sym in all_indices:
                if sym not in self._fetched_indices:
                    futures.append(executor.submit(self.get_index, sym))
            for sym in all_symbols:
                if sym not in self._fetched_stocks:
                    futures.append(executor.submit(self.get_stock, sym))
            concurrent.futures.wait(futures, timeout=120)

        # Warm up news
        executor_submit = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        executor_submit.submit(self.get_all_news)
        executor_submit.shutdown(wait=False)

    def get_stats(self) -> dict:
        return {
            "api_calls": self._api_calls,
            "indices_cached": len(self._fetched_indices),
            "stocks_cached": len(self._fetched_stocks),
        }


# 全局单例
_cache = None


def get_cache() -> DataCache:
    global _cache
    if _cache is None:
        _cache = DataCache()
    return _cache


def reset_cache():
    global _cache
    _cache = DataCache()