"""
Monitoring and Observability for Agentic Coding Assistant

This module provides comprehensive monitoring, metrics collection, and observability
for the agentic coding assistant system. It tracks agent performance, usage patterns,
and system health.
"""

import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import json
import statistics
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Metric:
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]
    metric_type: MetricType

@dataclass
class Alert:
    alert_id: str
    level: AlertLevel
    message: str
    timestamp: datetime
    agent_type: Optional[str] = None
    resolved: bool = False

@dataclass
class AgentPerformanceMetrics:
    agent_type: str
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    last_activity: datetime
    error_rate: float

@dataclass
class SystemHealthMetrics:
    cpu_usage: float
    memory_usage: float
    active_agents: int
    queue_size: int
    concurrent_tasks: int
    uptime_seconds: float
    last_health_check: datetime

class MetricsCollector:
    """Collects and stores metrics for the agentic system."""
    
    def __init__(self, max_metrics: int = 10000):
        self.metrics: deque = deque(maxlen=max_metrics)
        self.agent_metrics: Dict[str, AgentPerformanceMetrics] = {}
        self.system_metrics: SystemHealthMetrics = SystemHealthMetrics(
            cpu_usage=0.0,
            memory_usage=0.0,
            active_agents=0,
            queue_size=0,
            concurrent_tasks=0,
            uptime_seconds=0.0,
            last_health_check=datetime.now()
        )
        self.alerts: List[Alert] = []
        self.start_time = datetime.now()
        
        # Response time tracking
        self.response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Task tracking
        self.task_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: {"success": 0, "failure": 0})
        
        # Search integration metrics
        self.search_metrics = {
            "total_searches": 0,
            "successful_searches": 0,
            "failed_searches": 0,
            "average_search_time": 0.0,
            "context_retrieval_rate": 0.0
        }
    
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None, 
                     metric_type: MetricType = MetricType.GAUGE):
        """Record a metric."""
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {},
            metric_type=metric_type
        )
        
        self.metrics.append(metric)
        logger.debug(f"Recorded metric: {name}={value}")
    
    def record_agent_task(self, agent_type: str, task_type: str, 
                         success: bool, response_time: float):
        """Record agent task completion."""
        # Update agent metrics
        if agent_type not in self.agent_metrics:
            self.agent_metrics[agent_type] = AgentPerformanceMetrics(
                agent_type=agent_type,
                total_tasks=0,
                successful_tasks=0,
                failed_tasks=0,
                average_response_time=0.0,
                min_response_time=float('inf'),
                max_response_time=0.0,
                last_activity=datetime.now(),
                error_rate=0.0
            )
        
        metrics = self.agent_metrics[agent_type]
        metrics.total_tasks += 1
        metrics.last_activity = datetime.now()
        
        if success:
            metrics.successful_tasks += 1
            self.task_counts[agent_type]["success"] += 1
        else:
            metrics.failed_tasks += 1
            self.task_counts[agent_type]["failure"] += 1
        
        # Update response time statistics
        self.response_times[agent_type].append(response_time)
        times = list(self.response_times[agent_type])
        
        metrics.average_response_time = statistics.mean(times)
        metrics.min_response_time = min(times)
        metrics.max_response_time = max(times)
        metrics.error_rate = metrics.failed_tasks / metrics.total_tasks
        
        # Record metrics
        self.record_metric(f"agent.{agent_type}.response_time", response_time, 
                          {"agent": agent_type, "task": task_type}, MetricType.TIMER)
        self.record_metric(f"agent.{agent_type}.task_count", 1, 
                          {"agent": agent_type, "success": str(success)}, MetricType.COUNTER)
    
    def record_search_operation(self, search_type: str, success: bool, 
                               response_time: float, results_count: int = 0):
        """Record search operation metrics."""
        self.search_metrics["total_searches"] += 1
        
        if success:
            self.search_metrics["successful_searches"] += 1
            if results_count > 0:
                # Count as successful context retrieval
                total_retrievals = sum(1 for m in self.metrics 
                                     if m.name == "search.context_retrieval" and m.value > 0)
                self.search_metrics["context_retrieval_rate"] = total_retrievals / self.search_metrics["total_searches"]
        else:
            self.search_metrics["failed_searches"] += 1
        
        # Update average search time
        total_time = self.search_metrics["average_search_time"] * (self.search_metrics["total_searches"] - 1)
        self.search_metrics["average_search_time"] = (total_time + response_time) / self.search_metrics["total_searches"]
        
        # Record metrics
        self.record_metric(f"search.{search_type}.response_time", response_time, 
                          {"search_type": search_type}, MetricType.TIMER)
        self.record_metric(f"search.{search_type}.results_count", results_count, 
                          {"search_type": search_type}, MetricType.GAUGE)
        self.record_metric("search.context_retrieval", results_count, 
                          {"search_type": search_type}, MetricType.GAUGE)
    
    def update_system_health(self, cpu_usage: float = None, memory_usage: float = None,
                           active_agents: int = None, queue_size: int = None,
                           concurrent_tasks: int = None):
        """Update system health metrics."""
        if cpu_usage is not None:
            self.system_metrics.cpu_usage = cpu_usage
            self.record_metric("system.cpu_usage", cpu_usage, metric_type=MetricType.GAUGE)
        
        if memory_usage is not None:
            self.system_metrics.memory_usage = memory_usage
            self.record_metric("system.memory_usage", memory_usage, metric_type=MetricType.GAUGE)
        
        if active_agents is not None:
            self.system_metrics.active_agents = active_agents
            self.record_metric("system.active_agents", active_agents, metric_type=MetricType.GAUGE)
        
        if queue_size is not None:
            self.system_metrics.queue_size = queue_size
            self.record_metric("system.queue_size", queue_size, metric_type=MetricType.GAUGE)
        
        if concurrent_tasks is not None:
            self.system_metrics.concurrent_tasks = concurrent_tasks
            self.record_metric("system.concurrent_tasks", concurrent_tasks, metric_type=MetricType.GAUGE)
        
        self.system_metrics.uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        self.system_metrics.last_health_check = datetime.now()
    
    def create_alert(self, level: AlertLevel, message: str, agent_type: str = None):
        """Create an alert."""
        alert = Alert(
            alert_id=f"alert_{int(time.time())}_{len(self.alerts)}",
            level=level,
            message=message,
            timestamp=datetime.now(),
            agent_type=agent_type
        )
        
        self.alerts.append(alert)
        logger.warning(f"Alert created: {level.value} - {message}")
        
        return alert.alert_id
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                logger.info(f"Alert resolved: {alert_id}")
                break
    
    def get_metrics_summary(self, time_window: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Get a summary of metrics within a time window."""
        cutoff_time = datetime.now() - time_window
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
        
        summary = {
            "time_window": str(time_window),
            "total_metrics": len(recent_metrics),
            "agent_performance": {
                agent_type: asdict(metrics) for agent_type, metrics in self.agent_metrics.items()
            },
            "system_health": asdict(self.system_metrics),
            "search_integration": self.search_metrics.copy(),
            "active_alerts": len([a for a in self.alerts if not a.resolved]),
            "total_alerts": len(self.alerts),
            "uptime_hours": self.system_metrics.uptime_seconds / 3600
        }
        
        return summary
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get a detailed performance report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "system_overview": {
                "uptime": f"{self.system_metrics.uptime_seconds / 3600:.2f} hours",
                "total_agents": len(self.agent_metrics),
                "total_tasks_processed": sum(m.total_tasks for m in self.agent_metrics.values()),
                "overall_success_rate": self._calculate_overall_success_rate(),
                "average_response_time": self._calculate_average_response_time()
            },
            "agent_performance": {},
            "search_performance": self.search_metrics.copy(),
            "system_health": asdict(self.system_metrics),
            "recent_alerts": [asdict(a) for a in self.alerts[-10:]],  # Last 10 alerts
            "performance_trends": self._calculate_performance_trends()
        }
        
        # Add detailed agent performance
        for agent_type, metrics in self.agent_metrics.items():
            report["agent_performance"][agent_type] = {
                **asdict(metrics),
                "tasks_per_hour": self._calculate_tasks_per_hour(agent_type),
                "performance_score": self._calculate_performance_score(agent_type)
            }
        
        return report
    
    def _calculate_overall_success_rate(self) -> float:
        """Calculate overall system success rate."""
        total_success = sum(m.successful_tasks for m in self.agent_metrics.values())
        total_tasks = sum(m.total_tasks for m in self.agent_metrics.values())
        
        return (total_success / total_tasks) if total_tasks > 0 else 0.0
    
    def _calculate_average_response_time(self) -> float:
        """Calculate overall average response time."""
        all_times = []
        for times in self.response_times.values():
            all_times.extend(times)
        
        return statistics.mean(all_times) if all_times else 0.0
    
    def _calculate_tasks_per_hour(self, agent_type: str) -> float:
        """Calculate tasks per hour for an agent."""
        if agent_type not in self.agent_metrics:
            return 0.0
        
        metrics = self.agent_metrics[agent_type]
        uptime_hours = self.system_metrics.uptime_seconds / 3600
        
        return metrics.total_tasks / uptime_hours if uptime_hours > 0 else 0.0
    
    def _calculate_performance_score(self, agent_type: str) -> float:
        """Calculate a performance score for an agent."""
        if agent_type not in self.agent_metrics:
            return 0.0
        
        metrics = self.agent_metrics[agent_type]
        
        # Factors: success rate (40%), response time (30%), reliability (30%)
        success_score = (1 - metrics.error_rate) * 40
        
        # Response time score (lower is better, normalized to 0-30)
        avg_time = metrics.average_response_time
        time_score = max(0, 30 - (avg_time / 10)) if avg_time > 0 else 30
        
        # Reliability score based on consistent performance
        reliability_score = 30 if metrics.total_tasks > 10 else (metrics.total_tasks / 10) * 30
        
        return min(100, success_score + time_score + reliability_score)
    
    def _calculate_performance_trends(self) -> Dict[str, Any]:
        """Calculate performance trends over time."""
        # Get metrics from last 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
        
        # Group by hour
        hourly_data = defaultdict(lambda: {"tasks": 0, "response_times": [], "errors": 0})
        
        for metric in recent_metrics:
            hour_key = metric.timestamp.replace(minute=0, second=0, microsecond=0)
            
            if metric.name.endswith(".task_count"):
                hourly_data[hour_key]["tasks"] += 1
                if "success" in metric.labels and metric.labels["success"] == "False":
                    hourly_data[hour_key]["errors"] += 1
            elif metric.name.endswith(".response_time"):
                hourly_data[hour_key]["response_times"].append(metric.value)
        
        trends = {
            "hourly_task_volume": [],
            "hourly_error_rate": [],
            "hourly_avg_response_time": []
        }
        
        for hour, data in sorted(hourly_data.items()):
            trends["hourly_task_volume"].append({
                "hour": hour.isoformat(),
                "tasks": data["tasks"]
            })
            
            error_rate = data["errors"] / data["tasks"] if data["tasks"] > 0 else 0
            trends["hourly_error_rate"].append({
                "hour": hour.isoformat(),
                "error_rate": error_rate
            })
            
            avg_response = statistics.mean(data["response_times"]) if data["response_times"] else 0
            trends["hourly_avg_response_time"].append({
                "hour": hour.isoformat(),
                "avg_response_time": avg_response
            })
        
        return trends

class PerformanceMonitor:
    """Monitors system performance and generates alerts."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.monitoring_active = True
        
        # Thresholds for alerts
        self.thresholds = {
            "max_response_time": 30.0,  # seconds
            "max_error_rate": 0.1,  # 10%
            "max_queue_size": 100,
            "max_cpu_usage": 80.0,  # percentage
            "max_memory_usage": 85.0,  # percentage
            "min_success_rate": 0.9  # 90%
        }
    
    async def start_monitoring(self, check_interval: int = 60):
        """Start the monitoring loop."""
        logger.info("Starting performance monitoring")
        
        while self.monitoring_active:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(check_interval)
    
    async def _perform_health_checks(self):
        """Perform health checks and generate alerts if needed."""
        # Check agent performance
        for agent_type, metrics in self.metrics.agent_metrics.items():
            # Check error rate
            if metrics.error_rate > self.thresholds["max_error_rate"]:
                self.metrics.create_alert(
                    AlertLevel.WARNING,
                    f"High error rate for {agent_type}: {metrics.error_rate:.2%}",
                    agent_type
                )
            
            # Check response time
            if metrics.average_response_time > self.thresholds["max_response_time"]:
                self.metrics.create_alert(
                    AlertLevel.WARNING,
                    f"High response time for {agent_type}: {metrics.average_response_time:.2f}s",
                    agent_type
                )
        
        # Check system health
        system = self.metrics.system_metrics
        
        if system.cpu_usage > self.thresholds["max_cpu_usage"]:
            self.metrics.create_alert(
                AlertLevel.ERROR,
                f"High CPU usage: {system.cpu_usage:.1f}%"
            )
        
        if system.memory_usage > self.thresholds["max_memory_usage"]:
            self.metrics.create_alert(
                AlertLevel.ERROR,
                f"High memory usage: {system.memory_usage:.1f}%"
            )
        
        if system.queue_size > self.thresholds["max_queue_size"]:
            self.metrics.create_alert(
                AlertLevel.WARNING,
                f"Large queue size: {system.queue_size} tasks"
            )
        
        # Check search integration
        search_success_rate = (self.metrics.search_metrics["successful_searches"] / 
                             max(1, self.metrics.search_metrics["total_searches"]))
        
        if search_success_rate < self.thresholds["min_success_rate"]:
            self.metrics.create_alert(
                AlertLevel.ERROR,
                f"Low search success rate: {search_success_rate:.2%}"
            )
    
    def stop_monitoring(self):
        """Stop the monitoring loop."""
        self.monitoring_active = False
        logger.info("Performance monitoring stopped")

class MetricsExporter:
    """Exports metrics to various formats and destinations."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
    
    def export_to_json(self, filepath: str = None) -> str:
        """Export metrics to JSON format."""
        data = {
            "export_timestamp": datetime.now().isoformat(),
            "system_summary": self.metrics.get_metrics_summary(),
            "performance_report": self.metrics.get_performance_report(),
            "raw_metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "timestamp": m.timestamp.isoformat(),
                    "labels": m.labels,
                    "type": m.metric_type.value
                }
                for m in list(self.metrics.metrics)[-1000:]  # Last 1000 metrics
            ]
        }
        
        json_str = json.dumps(data, indent=2, default=str)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
            logger.info(f"Metrics exported to {filepath}")
        
        return json_str
    
    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        # Add agent metrics
        for agent_type, metrics in self.metrics.agent_metrics.items():
            lines.append(f'# HELP agent_total_tasks Total tasks processed by agent')
            lines.append(f'# TYPE agent_total_tasks counter')
            lines.append(f'agent_total_tasks{{agent="{agent_type}"}} {metrics.total_tasks}')
            
            lines.append(f'# HELP agent_success_rate Success rate of agent')
            lines.append(f'# TYPE agent_success_rate gauge')
            success_rate = 1 - metrics.error_rate
            lines.append(f'agent_success_rate{{agent="{agent_type}"}} {success_rate}')
            
            lines.append(f'# HELP agent_response_time_seconds Average response time')
            lines.append(f'# TYPE agent_response_time_seconds gauge')
            lines.append(f'agent_response_time_seconds{{agent="{agent_type}"}} {metrics.average_response_time}')
        
        # Add system metrics
        system = self.metrics.system_metrics
        lines.append(f'# HELP system_cpu_usage_percent CPU usage percentage')
        lines.append(f'# TYPE system_cpu_usage_percent gauge')
        lines.append(f'system_cpu_usage_percent {system.cpu_usage}')
        
        lines.append(f'# HELP system_memory_usage_percent Memory usage percentage')
        lines.append(f'# TYPE system_memory_usage_percent gauge')
        lines.append(f'system_memory_usage_percent {system.memory_usage}')
        
        return '\n'.join(lines)

# Global metrics collector instance
_global_metrics_collector: Optional[MetricsCollector] = None

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    return _global_metrics_collector

def setup_monitoring(metrics_collector: MetricsCollector = None) -> PerformanceMonitor:
    """Setup monitoring with the given or global metrics collector."""
    if metrics_collector is None:
        metrics_collector = get_metrics_collector()
    
    return PerformanceMonitor(metrics_collector)

# Decorators for automatic monitoring
def monitor_agent_task(agent_type: str, task_type: str):
    """Decorator to monitor agent task performance."""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                logger.error(f"Agent task failed: {e}")
                raise
            finally:
                response_time = time.time() - start_time
                get_metrics_collector().record_agent_task(agent_type, task_type, success, response_time)
        
        return wrapper
    return decorator

def monitor_search_operation(search_type: str):
    """Decorator to monitor search operations."""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            results_count = 0
            
            try:
                result = await func(*args, **kwargs)
                success = True
                
                # Try to extract results count
                if isinstance(result, dict):
                    if 'results' in result:
                        results_count = len(result['results'])
                    elif 'total_results' in result:
                        results_count = result['total_results']
                
                return result
            except Exception as e:
                logger.error(f"Search operation failed: {e}")
                raise
            finally:
                response_time = time.time() - start_time
                get_metrics_collector().record_search_operation(search_type, success, response_time, results_count)
        
        return wrapper
    return decorator
