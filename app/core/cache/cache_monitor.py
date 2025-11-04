import asyncio
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.core.cache.cache_stats import cache_stats_collector
from app.core.logging import logger


@dataclass
class CacheAlert:
    """缓存警报"""
    alert_type: str
    message: str
    severity: str  # info, warning, error, critical
    timestamp: datetime
    key: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None


class CacheMonitor:
    """
    缓存监控器，实时监控缓存性能和健康状况
    """

    def __init__(
        self,
        check_interval: int = 60,  # 检查间隔（秒）
        hit_rate_threshold: float = 0.8,  # 命中率阈值
        error_rate_threshold: float = 0.05,  # 错误率阈值
        response_time_threshold: float = 1.0,  # 响应时间阈值（秒）
        memory_usage_threshold: float = 0.9,  # 内存使用率阈值
        alert_cooldown: int = 300  # 警报冷却时间（秒）
    ):
        self.check_interval = check_interval
        self.hit_rate_threshold = hit_rate_threshold
        self.error_rate_threshold = error_rate_threshold
        self.response_time_threshold = response_time_threshold
        self.memory_usage_threshold = memory_usage_threshold
        self.alert_cooldown = alert_cooldown

        self._alerts: List[CacheAlert] = []
        self._alert_history: Dict[str, float] = {}  # alert_type -> last_alert_time
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None

        # 历史数据用于趋势分析
        self._history_data: Dict[str, List[Dict[str, any]]] = {
            'hit_rates': deque(maxlen=1440),  # 24小时的数据（每分钟一个点）
            'error_rates': deque(maxlen=1440),
            'response_times': deque(maxlen=1440),
            'memory_usage': deque(maxlen=1440)
        }

    async def start_monitoring(self) -> None:
        """开始监控"""
        if self._monitoring:
            logger.warning("Cache monitoring is already running")
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Cache monitoring started")

    async def stop_monitoring(self) -> None:
        """停止监控"""
        if not self._monitoring:
            return

        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("Cache monitoring stopped")

    async def _monitor_loop(self) -> None:
        """监控循环"""
        while self._monitoring:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache monitor loop: {str(e)}")
                await asyncio.sleep(self.check_interval)

    async def _perform_health_check(self) -> None:
        """执行健康检查"""
        try:
            # 获取当前统计信息
            stats = cache_stats_collector.get_cache_efficiency()
            performance = cache_stats_collector.get_performance_metrics()

            current_time = datetime.now()

            # 记录历史数据
            self._record_history_data(stats, performance)

            # 检查各项指标
            await self._check_hit_rate(stats['hit_rate'], current_time)
            await self._check_error_rate(stats['error_rate'], current_time)
            await self._check_response_time(performance['avg_response_time'], current_time)
            await self._check_memory_usage(current_time)

            # 检查趋势
            await self._check_trends(current_time)

            # 清理过期警报
            self._cleanup_old_alerts()

        except Exception as e:
            logger.error(f"Error during health check: {str(e)}")

    def _record_history_data(self, stats: Dict[str, float], performance: Dict[str, float]) -> None:
        """记录历史数据"""
        current_time = datetime.now()

        self._history_data['hit_rates'].append({
            'timestamp': current_time,
            'value': stats['hit_rate']
        })

        self._history_data['error_rates'].append({
            'timestamp': current_time,
            'value': stats['error_rate']
        })

        self._history_data['response_times'].append({
            'timestamp': current_time,
            'value': performance['avg_response_time']
        })

        # 模拟内存使用数据（实际实现中应该从缓存后端获取）
        self._history_data['memory_usage'].append({
            'timestamp': current_time,
            'value': self._estimate_memory_usage()
        })

    async def _check_hit_rate(self, hit_rate: float, current_time: datetime) -> None:
        """检查命中率"""
        if hit_rate < self.hit_rate_threshold * 0.5:  # 严重低于阈值
            await self._add_alert(
                'critical_hit_rate',
                f"Critical: Cache hit rate is {hit_rate}% (threshold: {self.hit_rate_threshold * 100}%)",
                'critical',
                current_time,
                value=hit_rate,
                threshold=self.hit_rate_threshold * 100
            )
        elif hit_rate < self.hit_rate_threshold:
            await self._add_alert(
                'low_hit_rate',
                f"Warning: Cache hit rate is {hit_rate}% (threshold: {self.hit_rate_threshold * 100}%)",
                'warning',
                current_time,
                value=hit_rate,
                threshold=self.hit_rate_threshold * 100
            )

    async def _check_error_rate(self, error_rate: float, current_time: datetime) -> None:
        """检查错误率"""
        if error_rate > self.error_rate_threshold * 2:  # 严重超过阈值
            await self._add_alert(
                'critical_error_rate',
                f"Critical: Cache error rate is {error_rate}% (threshold: {self.error_rate_threshold * 100}%)",
                'critical',
                current_time,
                value=error_rate,
                threshold=self.error_rate_threshold * 100
            )
        elif error_rate > self.error_rate_threshold:
            await self._add_alert(
                'high_error_rate',
                f"Warning: Cache error rate is {error_rate}% (threshold: {self.error_rate_threshold * 100}%)",
                'warning',
                current_time,
                value=error_rate,
                threshold=self.error_rate_threshold * 100
            )

    async def _check_response_time(self, avg_response_time: float, current_time: datetime) -> None:
        """检查响应时间"""
        if avg_response_time > self.response_time_threshold * 3:  # 严重超过阈值
            await self._add_alert(
                'critical_response_time',
                f"Critical: Cache response time is {avg_response_time}s (threshold: {self.response_time_threshold}s)",
                'critical',
                current_time,
                value=avg_response_time,
                threshold=self.response_time_threshold
            )
        elif avg_response_time > self.response_time_threshold:
            await self._add_alert(
                'slow_response_time',
                f"Warning: Cache response time is {avg_response_time}s (threshold: {self.response_time_threshold}s)",
                'warning',
                current_time,
                value=avg_response_time,
                threshold=self.response_time_threshold
            )

    async def _check_memory_usage(self, current_time: datetime) -> None:
        """检查内存使用"""
        memory_usage = self._estimate_memory_usage()

        if memory_usage > self.memory_usage_threshold * 100:
            await self._add_alert(
                'high_memory_usage',
                f"Warning: Cache memory usage is {memory_usage:.1f}% (threshold: {self.memory_usage_threshold * 100}%)",
                'warning',
                current_time,
                value=memory_usage,
                threshold=self.memory_usage_threshold * 100
            )

    async def _check_trends(self, current_time: datetime) -> None:
        """检查趋势"""
        if len(self._history_data['hit_rates']) < 10:
            return  # 数据不足，无法分析趋势

        # 分析命中率趋势
        recent_hit_rates = [d['value'] for d in list(self._history_data['hit_rates'])[-10:]]
        hit_rate_trend = self._calculate_trend(recent_hit_rates)

        if hit_rate_trend < -0.1:  # 命中率下降超过10%
            await self._add_alert(
                'hit_rate_declining',
                f"Info: Cache hit rate is declining (trend: {hit_rate_trend:.1%})",
                'info',
                current_time,
                value=hit_rate_trend
            )

        # 分析错误率趋势
        recent_error_rates = [d['value'] for d in list(self._history_data['error_rates'])[-10:]]
        error_rate_trend = self._calculate_trend(recent_error_rates)

        if error_rate_trend > 0.1:  # 错误率上升超过10%
            await self._add_alert(
                'error_rate_increasing',
                f"Warning: Cache error rate is increasing (trend: {error_rate_trend:.1%})",
                'warning',
                current_time,
                value=error_rate_trend
            )

    def _calculate_trend(self, values: List[float]) -> float:
        """计算趋势（简化版线性回归）"""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))

        if n * x2_sum - x_sum * x_sum == 0:
            return 0.0

        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        return slope / (y_sum / n) if y_sum != 0 else 0.0  # 归一化

    async def _add_alert(
        self,
        alert_type: str,
        message: str,
        severity: str,
        timestamp: datetime,
        key: Optional[str] = None,
        value: Optional[float] = None,
        threshold: Optional[float] = None
    ) -> None:
        """添加警报"""
        # 检查冷却时间
        last_alert_time = self._alert_history.get(alert_type, 0)
        current_time = time.time()

        if current_time - last_alert_time < self.alert_cooldown:
            return  # 还在冷却期内

        alert = CacheAlert(
            alert_type=alert_type,
            message=message,
            severity=severity,
            timestamp=timestamp,
            key=key,
            value=value,
            threshold=threshold
        )

        self._alerts.append(alert)
        self._alert_history[alert_type] = current_time

        # 根据严重程度记录日志
        if severity == 'critical':
            logger.critical(message)
        elif severity == 'error':
            logger.error(message)
        elif severity == 'warning':
            logger.warning(message)
        else:
            logger.info(message)

    def _cleanup_old_alerts(self) -> None:
        """清理过期警报"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        self._alerts = [alert for alert in self._alerts if alert.timestamp > cutoff_time]

    def _estimate_memory_usage(self) -> float:
        """估算内存使用率（模拟数据）"""
        # 实际实现中应该从缓存后端获取真实的内存使用数据
        # 这里返回一个模拟值
        import random
        return random.uniform(30, 85)

    def get_alerts(self, severity: Optional[str] = None, limit: int = 100) -> List[CacheAlert]:
        """获取警报"""
        alerts = self._alerts

        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]

        return alerts[-limit:]  # 返回最新的警报

    def get_health_status(self) -> Dict[str, any]:
        """获取健康状态"""
        recent_alerts = self.get_alerts(limit=10)

        # 计算健康分数（0-100）
        health_score = 100

        for alert in recent_alerts:
            if alert.severity == 'critical':
                health_score -= 25
            elif alert.severity == 'error':
                health_score -= 15
            elif alert.severity == 'warning':
                health_score -= 5

        health_score = max(0, health_score)

        # 获取当前指标
        stats = cache_stats_collector.get_cache_efficiency()
        performance = cache_stats_collector.get_performance_metrics()

        return {
            'health_score': health_score,
            'status': 'healthy' if health_score >= 80 else 'degraded' if health_score >= 60 else 'unhealthy',
            'current_metrics': {
                'hit_rate': stats['hit_rate'],
                'error_rate': stats['error_rate'],
                'avg_response_time': performance['avg_response_time']
            },
            'recent_alerts_count': len(recent_alerts),
            'monitoring_active': self._monitoring
        }

    def get_trend_analysis(self) -> Dict[str, any]:
        """获取趋势分析"""
        return {
            'hit_rate_trend': self._get_metric_trend('hit_rates'),
            'error_rate_trend': self._get_metric_trend('error_rates'),
            'response_time_trend': self._get_metric_trend('response_times'),
            'memory_usage_trend': self._get_metric_trend('memory_usage')
        }

    def _get_metric_trend(self, metric_name: str) -> Dict[str, any]:
        """获取指定指标的趋势"""
        data = list(self._history_data[metric_name])
        if len(data) < 10:
            return {'trend': 'insufficient_data', 'change': 0.0}

        recent_values = [d['value'] for d in data[-10:]]
        older_values = [d['value'] for d in data[-20:-10]] if len(data) >= 20 else recent_values[:5]

        if not older_values:
            return {'trend': 'stable', 'change': 0.0}

        recent_avg = sum(recent_values) / len(recent_values)
        older_avg = sum(older_values) / len(older_values)

        change = (recent_avg - older_avg) / max(older_avg, 0.001)

        if abs(change) < 0.05:
            trend = 'stable'
        elif change > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'

        return {
            'trend': trend,
            'change': round(change * 100, 2),  # 转换为百分比
            'recent_avg': round(recent_avg, 2),
            'older_avg': round(older_avg, 2)
        }


# 创建全局缓存监控器实例
cache_monitor = CacheMonitor()
