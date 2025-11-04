import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.core.logging import logger


@dataclass
class CacheMetric:
    """缓存指标数据类"""
    key: str
    hits: int
    misses: int
    errors: int
    avg_response_time: float
    last_accessed: datetime
    size_bytes: Optional[int] = None


class CacheStatsCollector:
    """
    缓存统计收集器，提供详细的缓存性能分析
    """

    def __init__(self, max_history_days: int = 7):
        self.max_history_days = max_history_days
        self._metrics: Dict[str, CacheMetric] = {}
        self._response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._daily_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {
            'hits': 0, 'misses': 0, 'errors': 0, 'total_requests': 0
        })
        self._start_time = time.time()

    def record_hit(self, key: str, response_time: float, size_bytes: Optional[int] = None) -> None:
        """记录缓存命中"""
        self._record_metric(key, 'hits', response_time, size_bytes)
        self._record_daily_stat('hits')

    def record_miss(self, key: str, response_time: float) -> None:
        """记录缓存未命中"""
        self._record_metric(key, 'misses', response_time)
        self._record_daily_stat('misses')

    def record_error(self, key: str, response_time: float, error: str) -> None:
        """记录缓存错误"""
        self._record_metric(key, 'errors', response_time)
        self._record_daily_stat('errors')
        logger.error(f"Cache error for key {key}: {error}")

    def _record_metric(self, key: str, metric_type: str, response_time: float,
                      size_bytes: Optional[int] = None) -> None:
        """内部方法：记录指标"""
        if key not in self._metrics:
            self._metrics[key] = CacheMetric(
                key=key,
                hits=0,
                misses=0,
                errors=0,
                avg_response_time=0.0,
                last_accessed=datetime.now()
            )

        metric = self._metrics[key]

        if metric_type == 'hits':
            metric.hits += 1
        elif metric_type == 'misses':
            metric.misses += 1
        elif metric_type == 'errors':
            metric.errors += 1

        metric.last_accessed = datetime.now()
        if size_bytes is not None:
            metric.size_bytes = size_bytes

        # 更新响应时间
        self._response_times[key].append(response_time)
        metric.avg_response_time = sum(self._response_times[key]) / len(self._response_times[key])

    def _record_daily_stat(self, stat_type: str) -> None:
        """记录每日统计"""
        today = datetime.now().strftime('%Y-%m-%d')
        self._daily_stats[today]['total_requests'] += 1
        self._daily_stats[today][stat_type] += 1

    def get_key_metrics(self, key: str) -> Optional[CacheMetric]:
        """获取指定键的指标"""
        return self._metrics.get(key)

    def get_top_keys(self, limit: int = 10, sort_by: str = 'hits') -> List[CacheMetric]:
        """
        获取热门缓存键

        :param limit: 返回数量限制
        :param sort_by: 排序字段 ('hits', 'misses', 'errors', 'avg_response_time')
        :return: 排序后的缓存指标列表
        """
        if sort_by not in ['hits', 'misses', 'errors', 'avg_response_time']:
            sort_by = 'hits'

        sorted_metrics = sorted(
            self._metrics.values(),
            key=lambda x: getattr(x, sort_by),
            reverse=True
        )

        return sorted_metrics[:limit]

    def get_cache_efficiency(self) -> Dict[str, float]:
        """获取缓存效率统计"""
        total_hits = sum(m.hits for m in self._metrics.values())
        total_misses = sum(m.misses for m in self._metrics.values())
        total_errors = sum(m.errors for m in self._metrics.values())
        total_requests = total_hits + total_misses + total_errors

        hit_rate = (total_hits / max(total_requests, 1)) * 100
        miss_rate = (total_misses / max(total_requests, 1)) * 100
        error_rate = (total_errors / max(total_requests, 1)) * 100

        return {
            'hit_rate': round(hit_rate, 2),
            'miss_rate': round(miss_rate, 2),
            'error_rate': round(error_rate, 2),
            'total_requests': total_requests,
            'total_hits': total_hits,
            'total_misses': total_misses,
            'total_errors': total_errors
        }

    def get_daily_stats(self, days: int = 7) -> Dict[str, Dict[str, int]]:
        """获取每日统计"""
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_stats = {}

        for date_str, stats in self._daily_stats.items():
            if datetime.strptime(date_str, '%Y-%m-%d') >= cutoff_date:
                filtered_stats[date_str] = stats

        return filtered_stats

    def get_performance_metrics(self) -> Dict[str, float]:
        """获取性能指标"""
        all_response_times = []
        for response_times in self._response_times.values():
            all_response_times.extend(response_times)

        if not all_response_times:
            return {
                'avg_response_time': 0.0,
                'p50_response_time': 0.0,
                'p95_response_time': 0.0,
                'p99_response_time': 0.0
            }

        sorted_times = sorted(all_response_times)

        return {
            'avg_response_time': round(sum(sorted_times) / len(sorted_times), 3),
            'p50_response_time': round(sorted_times[int(len(sorted_times) * 0.5)], 3),
            'p95_response_time': round(sorted_times[int(len(sorted_times) * 0.95)], 3),
            'p99_response_time': round(sorted_times[int(len(sorted_times) * 0.99)], 3)
        }

    def cleanup_old_metrics(self) -> int:
        """清理过期指标，返回清理数量"""
        cutoff_time = datetime.now() - timedelta(days=self.max_history_days)
        keys_to_remove = []

        for key, metric in self._metrics.items():
            if metric.last_accessed < cutoff_time:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._metrics[key]
            if key in self._response_times:
                del self._response_times[key]

        # 清理旧的每日统计
        cutoff_date = datetime.now() - timedelta(days=self.max_history_days)
        dates_to_remove = []

        for date_str in self._daily_stats.keys():
            if datetime.strptime(date_str, '%Y-%m-%d') < cutoff_date:
                dates_to_remove.append(date_str)

        for date_str in dates_to_remove:
            del self._daily_stats[date_str]

        total_removed = len(keys_to_remove) + len(dates_to_remove)
        if total_removed > 0:
            logger.info(f"Cleaned up {total_removed} old cache metrics")

        return total_removed

    def generate_report(self) -> Dict[str, any]:
        """生成完整报告"""
        return {
            'summary': self.get_cache_efficiency(),
            'performance': self.get_performance_metrics(),
            'top_keys': {
                'by_hits': [self._metric_to_dict(m) for m in self.get_top_keys(10, 'hits')],
                'by_misses': [self._metric_to_dict(m) for m in self.get_top_keys(10, 'misses')],
                'by_errors': [self._metric_to_dict(m) for m in self.get_top_keys(10, 'errors')]
            },
            'daily_stats': self.get_daily_stats(),
            'uptime_hours': round((time.time() - self._start_time) / 3600, 2)
        }

    def _metric_to_dict(self, metric: CacheMetric) -> Dict[str, any]:
        """将指标转换为字典"""
        return {
            'key': metric.key,
            'hits': metric.hits,
            'misses': metric.misses,
            'errors': metric.errors,
            'avg_response_time': metric.avg_response_time,
            'last_accessed': metric.last_accessed.isoformat(),
            'size_bytes': metric.size_bytes
        }


# 创建全局统计收集器实例
cache_stats_collector = CacheStatsCollector()
