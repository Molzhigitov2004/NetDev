from mpi4py import MPI
import random, time, os, math, csv, platform
from datetime import datetime

def estimate_pi_partial(n):
    inside = 0
    for _ in range(n):
        x = random.random()
        y = random.random()
        inside += (x*x + y*y <= 1.0)
    return inside

def get_system_info():
    return {"cpu_model": "intel core i7 13620h", "physical_cores": os.cpu_count(), "os_version": platform.platform(), "python_version": platform.python_version(),}

def run_once(comm, rank, size, N, run_id):
    local_n = N // size
    if rank == size - 1:
        local_n += N % size

    comm.Barrier()
    t0 = time.perf_counter()
    local_inside = estimate_pi_partial(local_n)
    total_inside = comm.reduce(local_inside, op=MPI.SUM, root=0)
    comm.Barrier()
    t1 = time.perf_counter()

    if rank == 0:
        elapsed = t1 - t0
        pi_est = 4.0 * total_inside / N
        error = abs(pi_est - math.pi)
        throughput = N / elapsed
        return { "timestamp": datetime.now().isoformat(), "platform": "VM", "workload": "mc_pi", "N": N, "P": size, "run_id": run_id,
            "runtime_s": round(elapsed, 6), "pi_estimate": round(pi_est, 6), "abs_error": round(error, 6), "throughput": round(throughput, 2) }
    return None

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    N = 10_000_000
    attempts = 3

    fieldnames = ["timestamp","platform","workload","N","P","run_id",
                  "runtime_s","pi_estimate","abs_error","throughput"]

    if rank == 0:
        file_exists = os.path.exists("results.csv") and os.path.getsize("results.csv") > 0
        f = open("results.csv", "a", newline="")
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

    for run_id in range(attempts):
        result = run_once(comm, rank, size, N, run_id)
        if rank == 0:
            writer.writerow(result)
            f.flush()
            print(f"[P={size}] run {run_id}: pi={result['pi_estimate']}, "
                  f"err={result['abs_error']}, time={result['runtime_s']}s, "
                  f"throughput={result['throughput']}")

    if rank == 0:
        f.close()
        info = get_system_info()
        print(f"\nSystem info: {info}")

if __name__ == "__main__":
    main()
