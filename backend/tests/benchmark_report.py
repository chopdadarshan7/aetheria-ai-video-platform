"""
API Benchmark Report — Aetheria Platform
Run standalone (not via pytest): python tests/benchmark_report.py

Measures: response times, throughput, and concurrent request handling.
"""
import time
import threading
import statistics
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.main import app
from app.database import Base, get_db
from app.config import settings

# ─── In-memory SQLite for benchmarking ───
engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

def override_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_db
client = TestClient(app, raise_server_exceptions=False)

# ─── Setup test user ───
client.post(f"{settings.API_V1_STR}/auth/register", json={
    "username": "benchuser", "email": "bench@test.com", "password": "BenchPass123!"
})
login = client.post(f"{settings.API_V1_STR}/auth/token", data={"username": "benchuser", "password": "BenchPass123!"})
TOKEN = login.json().get("access_token", "")
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def benchmark(label: str, fn, iterations: int = 50):
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        elapsed = (time.perf_counter() - start) * 1000  # ms
        times.append(elapsed)
    avg = statistics.mean(times)
    p95 = sorted(times)[int(0.95 * len(times))]
    p99 = sorted(times)[int(0.99 * len(times))]
    print(f"  {label:<45} avg={avg:6.1f}ms  p95={p95:6.1f}ms  p99={p99:6.1f}ms")
    return avg

def concurrent_benchmark(label: str, fn, concurrency: int = 20, iterations: int = 5):
    """Run fn with multiple concurrent threads, measure total throughput."""
    errors = []
    times = []
    def worker():
        for _ in range(iterations):
            start = time.perf_counter()
            try:
                fn()
            except Exception as e:
                errors.append(str(e))
            times.append((time.perf_counter() - start) * 1000)

    threads = [threading.Thread(target=worker) for _ in range(concurrency)]
    wall_start = time.perf_counter()
    for t in threads: t.start()
    for t in threads: t.join()
    wall_elapsed = time.perf_counter() - wall_start
    total_requests = concurrency * iterations
    rps = total_requests / wall_elapsed
    print(f"  {label:<45} {total_requests} reqs in {wall_elapsed:.2f}s = {rps:.1f} req/s  errors={len(errors)}")

print("\n" + "=" * 70)
print("  AETHERIA PLATFORM — API BENCHMARK REPORT")
print("=" * 70)

print("\n[LATENCY] Single-user response times (50 iterations each):")
benchmark("/health                               ", lambda: client.get("/health"))
benchmark("/healthz                              ", lambda: client.get("/healthz"))
benchmark(f"{settings.API_V1_STR}/users/me      ", lambda: client.get(f"{settings.API_V1_STR}/users/me", headers=HEADERS))
benchmark(f"{settings.API_V1_STR}/projects      ", lambda: client.get(f"{settings.API_V1_STR}/projects", headers=HEADERS))
benchmark(f"{settings.API_V1_STR}/renders       ", lambda: client.get(f"{settings.API_V1_STR}/renders", headers=HEADERS))
benchmark(f"{settings.API_V1_STR}/mlops/datasets", lambda: client.get(f"{settings.API_V1_STR}/mlops/datasets", headers=HEADERS))
benchmark(f"{settings.API_V1_STR}/saas/teams    ", lambda: client.get(f"{settings.API_V1_STR}/saas/teams", headers=HEADERS))

print("\n[THROUGHPUT] Concurrent users (20 threads × 5 iterations):")
concurrent_benchmark("/health — concurrent            ", lambda: client.get("/health"))
concurrent_benchmark("/projects — authenticated        ", lambda: client.get(f"{settings.API_V1_STR}/projects", headers=HEADERS))
concurrent_benchmark("/renders — authenticated         ", lambda: client.get(f"{settings.API_V1_STR}/renders", headers=HEADERS))

print("\n[WRITE OPERATIONS] POST latency (20 iterations):")
benchmark("POST /projects                        ", lambda: client.post(f"{settings.API_V1_STR}/projects", json={"name": "BenchProj"}, headers=HEADERS), iterations=20)
benchmark("POST /saas/teams                      ", lambda: client.post(f"{settings.API_V1_STR}/saas/teams", json={"name": "BenchTeam"}, headers=HEADERS), iterations=20)

print("\n" + "=" * 70)
print("  Benchmark complete.")
print("=" * 70 + "\n")
