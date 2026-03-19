"""
Load Testing Script for Taxi Bot - Fixed Version
Simulates 500 concurrent users performing realistic bot interactions
"""
import asyncio
import time
import random
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass, field
from collections import defaultdict
import logging

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not installed. System metrics will be limited.")

from aiogram import Bot
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.db import session_factory, engine, init_db

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise during load test
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class UserMetrics:
    """Metrics for a single simulated user"""
    user_id: int
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    response_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class LoadTestMetrics:
    """Aggregated metrics for the entire load test"""
    total_users: int = 500
    start_time: float = 0
    end_time: float = 0
    user_metrics: Dict[int, UserMetrics] = field(default_factory=dict)
    db_query_times: List[float] = field(default_factory=list)
    memory_samples: List[float] = field(default_factory=list)
    cpu_samples: List[float] = field(default_factory=list)
    endpoint_metrics: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    @property
    def total_requests(self) -> int:
        return sum(m.total_requests for m in self.user_metrics.values())

    @property
    def successful_requests(self) -> int:
        return sum(m.successful_requests for m in self.user_metrics.values())

    @property
    def failed_requests(self) -> int:
        return sum(m.failed_requests for m in self.user_metrics.values())

    @property
    def all_response_times(self) -> List[float]:
        times = []
        for m in self.user_metrics.values():
            times.extend(m.response_times)
        return times

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100


class SimulatedUser:
    """Simulates a single bot user"""

    def __init__(self, user_id: int, bot: Bot, metrics: LoadTestMetrics):
        self.user_id = user_id
        self.bot = bot
        self.metrics = metrics
        self.user_metrics = UserMetrics(user_id=user_id)
        metrics.user_metrics[user_id] = self.user_metrics

    async def _execute_action(self, action_name: str, action_func):
        """Execute an action and record metrics"""
        start_time = time.time()
        try:
            await action_func()
            elapsed = time.time() - start_time
            self.user_metrics.successful_requests += 1
            self.user_metrics.response_times.append(elapsed)
            self.metrics.endpoint_metrics[action_name].append(elapsed)
            return True
        except Exception as e:
            elapsed = time.time() - start_time
            self.user_metrics.failed_requests += 1
            self.user_metrics.errors.append(f"{action_name}: {str(e)}")
            logger.error(f"User {self.user_id} - {action_name} failed: {e}")
            return False
        finally:
            self.user_metrics.total_requests += 1

    async def simulate_start_command(self):
        """Simulate /start command - create user if not exists"""
        async def action():
            async with session_factory() as session:
                # Simple user creation without schema dependencies
                result = await session.execute(
                    text("SELECT COUNT(*) FROM users WHERE telegram_id = :user_id"),
                    {"user_id": self.user_id}
                )
                count = result.scalar()

                if count == 0:
                    # Insert new user with minimal required fields
                    await session.execute(
                        text("""
                        INSERT INTO users (telegram_id, username, tariffs, zones, notify_enabled, surge_threshold)
                        VALUES (:user_id, :username, 'econom', '', 0, 1.5)
                        """),
                        {
                            "user_id": self.user_id,
                            "username": f"loadtest_user_{self.user_id}"
                        }
                    )
                    await session.commit()

        return await self._execute_action("start_command", action)

    async def simulate_check_coefficients(self):
        """Simulate checking taxi coefficients"""
        async def action():
            async with session_factory() as session:
                # Check if coefficient_history table exists and query it
                result = await session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='coefficient_history'")
                )
                if result.scalar():
                    await session.execute(
                        text("SELECT * FROM coefficient_history ORDER BY timestamp DESC LIMIT 10")
                    )

        return await self._execute_action("check_coefficients", action)

    async def simulate_check_events(self):
        """Simulate checking events"""
        async def action():
            async with session_factory() as session:
                # Check if events table exists
                result = await session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
                )
                if result.scalar():
                    await session.execute(
                        text("SELECT * FROM events WHERE end_time >= datetime('now') LIMIT 5")
                    )

        return await self._execute_action("check_events", action)

    async def simulate_ai_advisor(self):
        """Simulate AI advisor usage"""
        async def action():
            async with session_factory() as session:
                # Check if ai_usage table exists
                result = await session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_usage'")
                )
                if result.scalar():
                    # Record AI usage with correct schema
                    await session.execute(
                        text("""
                        INSERT OR REPLACE INTO ai_usage (user_id, date, question_count)
                        VALUES (:user_id, :date, COALESCE((
                            SELECT question_count FROM ai_usage
                            WHERE user_id = :user_id AND date = :date
                        ), 0) + 1)
                        """),
                        {
                            "user_id": self.user_id,
                            "date": datetime.now().date()
                        }
                    )
                    await session.commit()

        return await self._execute_action("ai_advisor", action)

    async def simulate_add_shift(self):
        """Simulate adding a work shift"""
        async def action():
            async with session_factory() as session:
                # Check if shifts table exists
                result = await session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='shifts'")
                )
                if result.scalar():
                    # Add shift with correct field names
                    await session.execute(
                        text("""
                        INSERT INTO shifts (user_id, start_time, end_time, gross_earnings, trips_count, distance_km, net_earnings)
                        VALUES (:user_id, :start_time, :end_time, :gross_earnings, :trips_count, :distance_km, :net_earnings)
                        """),
                        {
                            "user_id": self.user_id,
                            "start_time": datetime.now() - timedelta(hours=random.uniform(4, 12)),
                            "end_time": datetime.now(),
                            "gross_earnings": random.uniform(500, 2000),
                            "trips_count": random.randint(10, 50),
                            "distance_km": random.uniform(50, 300),
                            "net_earnings": random.uniform(400, 1800)
                        }
                    )
                    await session.commit()

        return await self._execute_action("add_shift", action)

    async def simulate_check_statistics(self):
        """Simulate checking user statistics"""
        async def action():
            async with session_factory() as session:
                # Get user shifts if table exists
                result = await session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='shifts'")
                )
                if result.scalar():
                    await session.execute(
                        text("""
                        SELECT SUM(gross_earnings), SUM(net_earnings), COUNT(*), SUM(trips_count)
                        FROM shifts WHERE user_id = :user_id
                        """),
                        {"user_id": self.user_id}
                    )

        return await self._execute_action("check_statistics", action)

    async def simulate_update_settings(self):
        """Simulate updating user settings"""
        async def action():
            async with session_factory() as session:
                await session.execute(
                    text("UPDATE users SET surge_threshold = :threshold WHERE telegram_id = :user_id"),
                    {
                        "threshold": random.uniform(1.3, 2.0),
                        "user_id": self.user_id
                    }
                )
                await session.commit()

        return await self._execute_action("update_settings", action)

    async def simulate_check_achievements(self):
        """Simulate checking achievements"""
        async def action():
            async with session_factory() as session:
                # Check if user_achievements table exists
                result = await session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='user_achievements'")
                )
                if result.scalar():
                    await session.execute(
                        text("SELECT * FROM user_achievements WHERE user_id = :user_id"),
                        {"user_id": self.user_id}
                    )

        return await self._execute_action("check_achievements", action)

    async def run_user_session(self):
        """Simulate a realistic user session"""
        # Every user starts with /start
        await self.simulate_start_command()
        await asyncio.sleep(random.uniform(0.1, 0.5))

        # Simulate 5-15 actions per user
        num_actions = random.randint(5, 15)
        actions = [
            (self.simulate_check_coefficients, 0.3),  # 30% probability
            (self.simulate_check_events, 0.15),
            (self.simulate_ai_advisor, 0.1),
            (self.simulate_add_shift, 0.15),
            (self.simulate_check_statistics, 0.15),
            (self.simulate_update_settings, 0.05),
            (self.simulate_check_achievements, 0.1),
        ]

        for _ in range(num_actions):
            # Weighted random selection
            action_func = random.choices(
                [a[0] for a in actions],
                weights=[a[1] for a in actions]
            )[0]

            await action_func()
            # Random delay between actions (0.1-2 seconds)
            await asyncio.sleep(random.uniform(0.1, 2.0))


class LoadTester:
    """Main load testing orchestrator"""

    def __init__(self, num_users: int = 500):
        self.num_users = num_users
        self.metrics = LoadTestMetrics(total_users=num_users)
        self.bot = None

    async def monitor_system_resources(self):
        """Monitor system resources during the test"""
        if not PSUTIL_AVAILABLE:
            return

        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metrics.cpu_samples.append(cpu_percent)

                # Memory usage
                memory = psutil.virtual_memory()
                self.metrics.memory_samples.append(memory.percent)

                await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring resources: {e}")
                break

    async def measure_db_performance(self):
        """Measure database query performance"""
        queries = [
            ("SELECT COUNT(*) FROM users", "count_users"),
            ("SELECT COUNT(*) FROM shifts", "count_shifts"),
            ("SELECT COUNT(*) FROM ai_usage", "count_ai_usage"),
        ]

        for query, name in queries:
            start_time = time.time()
            try:
                async with session_factory() as session:
                    # Check if table exists first
                    table_name = query.split("FROM")[1].strip().split()[0]
                    result = await session.execute(
                        text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                    )
                    if result.scalar():
                        await session.execute(text(query))
                elapsed = time.time() - start_time
                self.metrics.db_query_times.append(elapsed)
            except Exception as e:
                logger.error(f"DB query {name} failed: {e}")

    async def run_load_test(self):
        """Execute the load test"""
        print(f"\n{'='*80}")
        print(f"TAXI BOT LOAD TEST - {self.num_users} CONCURRENT USERS")
        print(f"{'='*80}\n")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Initializing bot and database...")

        # Initialize database
        await init_db()

        # Initialize bot
        self.bot = Bot(token=settings.bot_token)

        # Start system monitoring
        monitor_task = None
        if PSUTIL_AVAILABLE:
            monitor_task = asyncio.create_task(self.monitor_system_resources())

        self.metrics.start_time = time.time()

        print(f"\nSpawning {self.num_users} simulated users...")
        print("This may take several minutes...\n")

        # Create simulated users
        users = [SimulatedUser(1000000 + i, self.bot, self.metrics) for i in range(self.num_users)]

        # Run users in batches to avoid overwhelming the system
        batch_size = 50
        batches = [users[i:i + batch_size] for i in range(0, len(users), batch_size)]

        for batch_num, batch in enumerate(batches, 1):
            print(f"Running batch {batch_num}/{len(batches)} ({len(batch)} users)...")
            tasks = [user.run_user_session() for user in batch]
            await asyncio.gather(*tasks, return_exceptions=True)
            # Small delay between batches
            await asyncio.sleep(1)

        self.metrics.end_time = time.time()

        # Stop monitoring
        if monitor_task:
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass

        # Measure final DB performance
        print("\nMeasuring database performance...")
        await self.measure_db_performance()

        # Close bot session
        await self.bot.session.close()

        print(f"\nLoad test completed!")
        print(f"Duration: {self.metrics.duration:.2f} seconds")
        print(f"Total requests: {self.metrics.total_requests}")
        print(f"Success rate: {self.metrics.success_rate:.2f}%")

    def generate_report(self) -> str:
        """Generate detailed load test report"""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("TAXI BOT LOAD TEST REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"\nTest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Duration: {self.metrics.duration:.2f} seconds")
        report_lines.append(f"\n{'-' * 80}")
        report_lines.append("OVERVIEW")
        report_lines.append("-" * 80)
        report_lines.append(f"Total Simulated Users: {self.metrics.total_users}")
        report_lines.append(f"Total Requests: {self.metrics.total_requests}")
        report_lines.append(f"Successful Requests: {self.metrics.successful_requests}")
        report_lines.append(f"Failed Requests: {self.metrics.failed_requests}")
        report_lines.append(f"Success Rate: {self.metrics.success_rate:.2f}%")
        report_lines.append(f"Requests per Second: {self.metrics.total_requests / self.metrics.duration:.2f}")

        # Response time statistics
        if self.metrics.all_response_times:
            response_times = self.metrics.all_response_times
            report_lines.append(f"\n{'-' * 80}")
            report_lines.append("RESPONSE TIME STATISTICS")
            report_lines.append("-" * 80)
            report_lines.append(f"Mean: {statistics.mean(response_times):.3f}s")
            report_lines.append(f"Median: {statistics.median(response_times):.3f}s")
            report_lines.append(f"Min: {min(response_times):.3f}s")
            report_lines.append(f"Max: {max(response_times):.3f}s")
            report_lines.append(f"Std Dev: {statistics.stdev(response_times) if len(response_times) > 1 else 0:.3f}s")

            # Percentiles
            sorted_times = sorted(response_times)
            p50 = sorted_times[int(len(sorted_times) * 0.50)]
            p90 = sorted_times[int(len(sorted_times) * 0.90)]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]

            report_lines.append(f"\nPercentiles:")
            report_lines.append(f"  P50: {p50:.3f}s")
            report_lines.append(f"  P90: {p90:.3f}s")
            report_lines.append(f"  P95: {p95:.3f}s")
            report_lines.append(f"  P99: {p99:.3f}s")

        # Endpoint-specific metrics
        if self.metrics.endpoint_metrics:
            report_lines.append(f"\n{'-' * 80}")
            report_lines.append("ENDPOINT PERFORMANCE")
            report_lines.append("-" * 80)
            for endpoint, times in sorted(self.metrics.endpoint_metrics.items()):
                if times:
                    report_lines.append(f"\n{endpoint}:")
                    report_lines.append(f"  Requests: {len(times)}")
                    report_lines.append(f"  Mean: {statistics.mean(times):.3f}s")
                    report_lines.append(f"  Median: {statistics.median(times):.3f}s")
                    report_lines.append(f"  Max: {max(times):.3f}s")

        # System resource usage
        if self.metrics.memory_samples or self.metrics.cpu_samples:
            report_lines.append(f"\n{'-' * 80}")
            report_lines.append("SYSTEM RESOURCE USAGE")
            report_lines.append("-" * 80)

            if self.metrics.cpu_samples:
                report_lines.append(f"\nCPU Usage:")
                report_lines.append(f"  Mean: {statistics.mean(self.metrics.cpu_samples):.1f}%")
                report_lines.append(f"  Max: {max(self.metrics.cpu_samples):.1f}%")

            if self.metrics.memory_samples:
                report_lines.append(f"\nMemory Usage:")
                report_lines.append(f"  Mean: {statistics.mean(self.metrics.memory_samples):.1f}%")
                report_lines.append(f"  Max: {max(self.metrics.memory_samples):.1f}%")

        # Database performance
        if self.metrics.db_query_times:
            report_lines.append(f"\n{'-' * 80}")
            report_lines.append("DATABASE PERFORMANCE")
            report_lines.append("-" * 80)
            report_lines.append(f"Average Query Time: {statistics.mean(self.metrics.db_query_times):.3f}s")
            report_lines.append(f"Max Query Time: {max(self.metrics.db_query_times):.3f}s")

        # Error analysis
        all_errors = []
        for user_metric in self.metrics.user_metrics.values():
            all_errors.extend(user_metric.errors)

        if all_errors:
            report_lines.append(f"\n{'-' * 80}")
            report_lines.append("ERROR ANALYSIS")
            report_lines.append("-" * 80)
            report_lines.append(f"Total Errors: {len(all_errors)}")

            # Group errors by type
            error_counts = defaultdict(int)
            for error in all_errors:
                error_type = error.split(":")[0] if ":" in error else error
                error_counts[error_type] += 1

            report_lines.append(f"\nError Breakdown:")
            for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                report_lines.append(f"  {error_type}: {count}")

            # Show sample errors
            report_lines.append(f"\nSample Errors (first 10):")
            for error in all_errors[:10]:
                report_lines.append(f"  - {error}")

        # Recommendations
        report_lines.append(f"\n{'-' * 80}")
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 80)

        recommendations = []

        # Success rate recommendations
        if self.metrics.success_rate < 95:
            recommendations.append("[!] Success rate is below 95%. Investigate error logs and improve error handling.")
        elif self.metrics.success_rate < 99:
            recommendations.append("[*] Success rate is good but could be improved. Review failed requests.")
        else:
            recommendations.append("[+] Excellent success rate!")

        # Response time recommendations
        if self.metrics.all_response_times:
            mean_time = statistics.mean(self.metrics.all_response_times)
            if mean_time > 1.0:
                recommendations.append("[!] Average response time exceeds 1 second. Consider:")
                recommendations.append("   - Adding database indexes")
                recommendations.append("   - Implementing caching (Redis)")
                recommendations.append("   - Optimizing slow queries")
            elif mean_time > 0.5:
                recommendations.append("[*] Response times are acceptable but could be optimized.")
            else:
                recommendations.append("[+] Response times are excellent!")

        # Resource usage recommendations
        if self.metrics.cpu_samples and max(self.metrics.cpu_samples) > 80:
            recommendations.append("[!] High CPU usage detected. Consider:")
            recommendations.append("   - Scaling horizontally (multiple bot instances)")
            recommendations.append("   - Optimizing CPU-intensive operations")

        if self.metrics.memory_samples and max(self.metrics.memory_samples) > 80:
            recommendations.append("[!] High memory usage detected. Consider:")
            recommendations.append("   - Implementing connection pooling")
            recommendations.append("   - Reviewing memory leaks")

        # Scalability recommendations
        rps = self.metrics.total_requests / self.metrics.duration
        if rps < 50:
            recommendations.append("[!] Low throughput detected. System may struggle with high load.")
        elif rps < 100:
            recommendations.append("[*] Moderate throughput. Consider optimization for better scalability.")
        else:
            recommendations.append("[+] Good throughput for current load!")

        # Database recommendations
        if self.metrics.db_query_times:
            max_query_time = max(self.metrics.db_query_times)
            if max_query_time > 0.5:
                recommendations.append("[!] Slow database queries detected. Consider:")
                recommendations.append("   - Adding indexes on frequently queried columns")
                recommendations.append("   - Migrating to PostgreSQL for better performance")
                recommendations.append("   - Implementing query result caching")

        for rec in recommendations:
            report_lines.append(rec)

        report_lines.append(f"\n{'=' * 80}")
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 80)

        return "\n".join(report_lines)


async def main():
    """Main entry point"""
    print("\n[*] Starting Taxi Bot Load Test...")

    # Create and run load tester
    tester = LoadTester(num_users=500)

    try:
        await tester.run_load_test()
    except KeyboardInterrupt:
        print("\n\n[!] Load test interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Load test failed: {e}")
        logger.exception("Load test failed")
        return

    # Generate and save report
    print("\n[*] Generating report...")
    report = tester.generate_report()

    # Save to file
    report_filename = f"LOAD_TEST_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n[SUCCESS] Report saved to: {report_filename}")
    print("\n" + "=" * 80)
    print(report)


if __name__ == "__main__":
    asyncio.run(main())