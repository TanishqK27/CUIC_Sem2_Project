#!/usr/bin/env python3
"""Parallel NBA box score collection via proxy rotation.

Distributes box score collection across N local workers, each using a
different proxy IP to avoid rate limiting.

Usage:
    # Using a proxy file (webshare.io, etc.) — recommended
    python scripts/parallel_nba_collect.py --proxy-file proxies.txt
    python scripts/parallel_nba_collect.py --proxy-file proxies.txt --seasons 2024-25

    # Using DigitalOcean droplets as proxies
    python scripts/parallel_nba_collect.py --ssh-key-id 12345678 --num-workers 50

    # Worker mode (called by orchestrator, not by user)
    python scripts/parallel_nba_collect.py --worker --worker-id 3 \
        --games-file data/worker-3/games.json --output-dir data/worker-3

Proxy file format (one per line):
    ip:port:username:password     (webshare.io default)
    socks5://user:pass@ip:port    (full URL)

Prerequisites:
    pip install pysocks
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DROPLET_NAME_PREFIX = "nba-proxy"
DROPLET_TAG = "nba-parallel-collect"
BASE_SOCKS_PORT = 1081
WORKER_REQUEST_DELAY = "0.5"
MAX_PARALLEL_WORKERS = 99  # cap to leave headroom


# ---------------------------------------------------------------------------
# Infrastructure helpers
# ---------------------------------------------------------------------------

def create_droplets(
    num: int,
    size: str,
    region: str,
    ssh_key_id: str,
    image: str,
) -> list[str]:
    """Create DigitalOcean droplets via doctl. Returns list of droplet names."""
    names = [f"{DROPLET_NAME_PREFIX}-{i}" for i in range(num)]
    names_str = " ".join(names)

    print(f"  Creating {num} droplets ({size} in {region})...")
    cmd = (
        f"doctl compute droplet create {names_str} "
        f"--size {size} --region {region} --image {image} "
        f"--ssh-keys {ssh_key_id} --tag-name {DROPLET_TAG} "
        f"--wait --no-header --format ID"
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create droplets: {result.stderr}")

    print(f"  -> {num} droplets created")
    return names


def wait_for_droplet_ips(num: int, max_wait: int = 300) -> list[dict]:
    """Poll doctl until all tagged droplets have public IPs.

    Returns:
        List of dicts with 'name' and 'ip' keys.
    """
    print("  Waiting for droplet IPs...")
    start = time.time()

    while time.time() - start < max_wait:
        cmd = (
            f"doctl compute droplet list --tag-name {DROPLET_TAG} "
            f"--no-header --format Name,PublicIPv4"
        )
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            time.sleep(5)
            continue

        droplets = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[1] and parts[1] != "":
                droplets.append({"name": parts[0], "ip": parts[1]})

        if len(droplets) >= num:
            print(f"  -> {len(droplets)} droplets ready")
            return droplets

        elapsed = int(time.time() - start)
        print(f"  ... {len(droplets)}/{num} have IPs ({elapsed}s elapsed)")
        time.sleep(10)

    raise TimeoutError(f"Only {len(droplets)}/{num} droplets got IPs within {max_wait}s")


def open_ssh_tunnels(droplets: list[dict]) -> list[int]:
    """Open SOCKS5 tunnels to each droplet. Returns list of local ports.

    Each tunnel runs as a background process:
        ssh -D {port} -N -f -o StrictHostKeyChecking=no root@{ip}
    """
    print(f"  Opening {len(droplets)} SSH tunnels...")
    ports = []
    tunnel_pids = []

    for i, droplet in enumerate(droplets):
        port = BASE_SOCKS_PORT + i
        ip = droplet["ip"]

        # Retry SSH a few times (droplet might not be ready for SSH yet)
        for attempt in range(10):
            cmd = (
                f"ssh -D {port} -N -f "
                f"-o StrictHostKeyChecking=no "
                f"-o UserKnownHostsFile=/dev/null "
                f"-o ConnectTimeout=10 "
                f"-o LogLevel=ERROR "
                f"root@{ip}"
            )
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                ports.append(port)
                break
            if attempt < 9:
                time.sleep(5)
        else:
            print(f"  WARNING: Failed to open tunnel to {ip} after 10 attempts")
            ports.append(port)  # still add so indexing stays aligned

    print(f"  -> {len(ports)} tunnels open (ports {ports[0]}-{ports[-1]})")
    return ports


def destroy_droplets() -> None:
    """Destroy all droplets with the collection tag."""
    print(f"\n  Destroying droplets tagged '{DROPLET_TAG}'...")
    cmd = (
        f"doctl compute droplet delete --tag-name {DROPLET_TAG} --force"
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("  -> All proxy droplets destroyed")
    else:
        print(f"  WARNING: Failed to destroy droplets: {result.stderr}")
        print(f"  Run manually: doctl compute droplet delete --tag-name {DROPLET_TAG} --force")


# ---------------------------------------------------------------------------
# Proxy health check
# ---------------------------------------------------------------------------

def check_proxy(proxy_url: str, timeout: int = 15) -> bool:
    """Test a single proxy by making a request through it.

    Uses httpbin.org for connectivity check since stats.nba.com
    requires specific headers that only nba_api provides.

    Returns:
        True if proxy is working, False otherwise.
    """
    import requests

    try:
        resp = requests.get(
            "https://httpbin.org/ip",
            proxies={"https": proxy_url, "http": proxy_url},
            timeout=timeout,
        )
        return resp.status_code == 200
    except Exception:
        return False


def validate_proxies(
    proxy_urls: list[str],
    max_concurrent: int = 20,
    timeout: int = 15,
) -> list[str]:
    """Test all proxies in parallel and return only working ones.

    Args:
        proxy_urls: List of proxy URLs to test.
        max_concurrent: Max threads for parallel testing.
        timeout: Seconds to wait per proxy.

    Returns:
        List of working proxy URLs.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from tqdm import tqdm

    working = []
    failed = []

    bar = tqdm(total=len(proxy_urls), desc="Validating proxies", unit="proxy")
    with ThreadPoolExecutor(max_workers=max_concurrent) as pool:
        futures = {
            pool.submit(check_proxy, url, timeout): url
            for url in proxy_urls
        }
        for future in as_completed(futures):
            url = futures[future]
            proxy_display = url.split("@")[-1] if "@" in url else url
            try:
                if future.result():
                    working.append(url)
                else:
                    failed.append(proxy_display)
            except Exception:
                failed.append(proxy_display)
            bar.update(1)
            bar.set_postfix_str(f"{len(working)} working")
    bar.close()

    if failed:
        print(f"  Dropped {len(failed)} bad proxies: {', '.join(failed[:5])}"
              + (f" ... and {len(failed)-5} more" if len(failed) > 5 else ""))

    return working


# ---------------------------------------------------------------------------
# Proxy file helpers
# ---------------------------------------------------------------------------

def parse_proxy_file(path: str) -> list[str]:
    """Parse a proxy list file into SOCKS5h URLs (remote DNS resolution).

    Supports formats:
        ip:port:username:password   (webshare.io default)
        socks5://user:pass@ip:port  (full URL, upgraded to socks5h)
    """
    from urllib.parse import quote

    proxies = []
    for line in Path(path).read_text().strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("socks5://") or line.startswith("socks4://"):
            # Upgrade socks5:// to socks5h:// for remote DNS
            proxies.append(line.replace("socks5://", "socks5h://", 1))
        elif line.startswith("socks5h://"):
            proxies.append(line)
        else:
            parts = line.split(":")
            if len(parts) == 4:
                ip, port, user, pw = parts
                # URL-encode credentials in case of special characters
                user_enc = quote(user, safe="")
                pw_enc = quote(pw, safe="")
                proxies.append(f"socks5h://{user_enc}:{pw_enc}@{ip}:{port}")
            elif len(parts) == 2:
                ip, port = parts
                proxies.append(f"socks5h://{ip}:{port}")
            else:
                print(f"  WARNING: Skipping unrecognized proxy line: {line}")
    return proxies


# ---------------------------------------------------------------------------
# Game discovery (local, fast)
# ---------------------------------------------------------------------------

def discover_all_games(
    seasons: list[str] | None,
    output_dir: str = "data",
) -> list[dict]:
    """Run phases 1-3 locally to get game IDs with OT info.

    Also saves nba_games.csv so downstream steps (features, etc.)
    don't need to re-discover games.

    Args:
        seasons: Seasons to discover.
        output_dir: Directory to save nba_games.csv.

    Returns:
        List of dicts with 'game_id' and 'num_ot' keys.
    """
    from cuic_quant.data.nba.constants import CSV_CONFIG, SEASONS
    from cuic_quant.data.nba.csv_writer import save_csv
    from cuic_quant.data.nba.games import collect_quarter_scores, discover_games

    seasons = seasons or SEASONS

    print("\n  Phase 1-3: Discovering games locally...")
    games_df = discover_games(seasons=seasons)
    if games_df.empty:
        raise RuntimeError("No games discovered")

    print(f"  -> {len(games_df):,} games found, collecting quarter scores...")
    games_df = collect_quarter_scores(games_df)

    # Save games CSV for downstream use (features pipeline, etc.)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    save_csv(games_df, out / CSV_CONFIG["nba_games"]["file"], CSV_CONFIG["nba_games"]["pk"])
    print(f"  -> Saved {len(games_df):,} games to {out / CSV_CONFIG['nba_games']['file']}")

    games = []
    for _, row in games_df.iterrows():
        games.append({
            "game_id": str(row["game_id"]),
            "num_ot": int(row.get("num_ot") or 0),
        })

    print(f"  -> {len(games):,} games ready for distribution")
    return games


def split_games(games: list[dict], num_chunks: int) -> list[list[dict]]:
    """Split games into roughly equal chunks."""
    chunk_size = math.ceil(len(games) / num_chunks)
    return [games[i : i + chunk_size] for i in range(0, len(games), chunk_size)]


# ---------------------------------------------------------------------------
# Worker management
# ---------------------------------------------------------------------------

def launch_workers(
    num_workers: int,
    proxy_urls: list[str],
    game_chunks: list[list[dict]],
    output_base: str,
) -> list[subprocess.Popen]:
    """Launch worker subprocesses, each with its own proxy and game chunk."""
    project_dir = Path(__file__).resolve().parent.parent
    python = sys.executable
    script = str(Path(__file__).resolve())

    workers = []
    log_handles = []
    for i in range(min(num_workers, len(game_chunks))):
        worker_dir = Path(output_base) / f"worker-{i}"
        worker_dir.mkdir(parents=True, exist_ok=True)
        log_dir = project_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        # Write game IDs for this worker
        games_file = worker_dir / "games.json"
        games_file.write_text(json.dumps(game_chunks[i], indent=2))

        # Worker env
        env = os.environ.copy()
        env["NBA_PROXY"] = proxy_urls[i]
        env["NBA_REQUEST_DELAY"] = WORKER_REQUEST_DELAY
        env["PYTHONPATH"] = str(project_dir / "src") + (
            f":{env['PYTHONPATH']}" if env.get("PYTHONPATH") else ""
        )

        log_file = log_dir / f"worker-{i}.log"

        cmd = [
            python, script,
            "--worker",
            "--worker-id", str(i),
            "--games-file", str(games_file),
            "--output-dir", str(worker_dir),
        ]

        log_fh = open(log_file, "w")
        log_handles.append(log_fh)
        proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
        )
        workers.append(proc)
        # Mask credentials in output
        proxy_display = proxy_urls[i].split("@")[-1] if "@" in proxy_urls[i] else proxy_urls[i]
        print(f"  Worker {i}: PID {proc.pid}, proxy {proxy_display}, {len(game_chunks[i])} games")

    return workers, log_handles


def _get_worker_progress(output_base: str, worker_id: int) -> int:
    """Get number of games completed by a worker from its checkpoint."""
    ckpt_path = Path(output_base) / f"worker-{worker_id}" / ".nba_checkpoint.json"
    if ckpt_path.exists():
        try:
            ckpt = json.loads(ckpt_path.read_text())
            return len(ckpt.get("games_collected", {}).get("boxscores", []))
        except (json.JSONDecodeError, KeyError):
            pass
    return 0


def _get_remaining_games(output_base: str, worker_id: int) -> list[dict]:
    """Get games a worker hasn't completed yet."""
    worker_dir = Path(output_base) / f"worker-{worker_id}"
    games_file = worker_dir / "games.json"
    ckpt_file = worker_dir / ".nba_checkpoint.json"

    if not games_file.exists():
        return []

    all_games = json.loads(games_file.read_text())
    done_ids: set[str] = set()
    if ckpt_file.exists():
        try:
            ckpt = json.loads(ckpt_file.read_text())
            done_ids = set(ckpt.get("games_collected", {}).get("boxscores", []))
        except (json.JSONDecodeError, KeyError):
            pass

    return [g for g in all_games if g["game_id"] not in done_ids]


def _respawn_worker(
    worker_id: int,
    games: list[dict],
    proxy_url: str,
    output_base: str,
) -> tuple[subprocess.Popen, "IO"]:
    """Spawn a replacement worker for stalled games."""
    project_dir = Path(__file__).resolve().parent.parent
    python = sys.executable
    script = str(Path(__file__).resolve())

    worker_dir = Path(output_base) / f"worker-{worker_id}"
    worker_dir.mkdir(parents=True, exist_ok=True)
    games_file = worker_dir / "games.json"
    games_file.write_text(json.dumps(games, indent=2))

    env = os.environ.copy()
    env["NBA_PROXY"] = proxy_url
    env["NBA_REQUEST_DELAY"] = WORKER_REQUEST_DELAY
    env["PYTHONPATH"] = str(project_dir / "src") + (
        f":{env['PYTHONPATH']}" if env.get("PYTHONPATH") else ""
    )

    log_file = project_dir / "logs" / f"worker-{worker_id}.log"
    log_fh = open(log_file, "a")

    cmd = [
        python, script,
        "--worker",
        "--worker-id", str(worker_id),
        "--games-file", str(games_file),
        "--output-dir", str(worker_dir),
    ]

    proc = subprocess.Popen(
        cmd, env=env, stdout=log_fh, stderr=subprocess.STDOUT,
    )
    return proc, log_fh


def monitor_workers(
    workers: list[subprocess.Popen],
    output_base: str,
    total_games: int,
    proxy_urls: list[str] | None = None,
    stall_timeout: int = 180,
) -> None:
    """Poll workers until all complete, showing a tqdm progress bar.

    If a worker makes no progress for stall_timeout seconds, it is killed
    and its remaining games are reassigned to a replacement worker using
    a known-good proxy.

    Args:
        workers: List of worker Popen objects.
        output_base: Base directory containing worker-N/ subdirectories.
        total_games: Total number of games to collect.
        proxy_urls: List of proxy URLs (needed for respawning stalled workers).
        stall_timeout: Seconds with no progress before a worker is killed.
    """
    from tqdm import tqdm

    num_workers = len(workers)

    bar = tqdm(
        total=total_games,
        desc="Box scores",
        unit="game",
        dynamic_ncols=True,
        bar_format=(
            "{l_bar}{bar}| {n_fmt}/{total_fmt} games "
            "[{elapsed}<{remaining}, {rate_fmt}, "
            "{postfix}]"
        ),
    )

    prev_done = 0
    # Track per-worker progress for stall detection
    worker_progress: dict[int, int] = {i: 0 for i in range(num_workers)}
    worker_last_change: dict[int, float] = {i: time.time() for i in range(num_workers)}
    respawned: set[int] = set()
    extra_log_handles: list = []

    while True:
        alive = sum(1 for w in workers if w.poll() is None)
        workers_done = num_workers - alive

        # Count games done across all workers
        games_done = 0
        errors = 0
        for i in range(num_workers):
            prog = _get_worker_progress(output_base, i)
            games_done += prog

            ckpt_path = Path(output_base) / f"worker-{i}" / ".nba_checkpoint.json"
            if ckpt_path.exists():
                try:
                    ckpt = json.loads(ckpt_path.read_text())
                    errors += len(ckpt.get("errors", []))
                except (json.JSONDecodeError, KeyError):
                    pass

            # Stall detection
            if prog != worker_progress[i]:
                worker_progress[i] = prog
                worker_last_change[i] = time.time()

        # Check for stalled workers
        now = time.time()
        for i in range(num_workers):
            if workers[i].poll() is not None:
                continue  # already finished
            if i in respawned:
                continue  # already respawned once
            stall_time = now - worker_last_change[i]
            if stall_time > stall_timeout and proxy_urls:
                remaining = _get_remaining_games(output_base, i)
                if not remaining:
                    continue

                # Kill stalled worker
                workers[i].terminate()
                workers[i].wait(timeout=10)

                # Pick a proxy from a worker that already finished successfully
                good_proxy = None
                for j in range(num_workers):
                    if j != i and workers[j].poll() is not None and workers[j].returncode == 0:
                        good_proxy = proxy_urls[j]
                        break
                if not good_proxy:
                    good_proxy = proxy_urls[0] if proxy_urls[0] != proxy_urls[i] else proxy_urls[1]

                bar.write(
                    f"  Worker {i} stalled ({int(stall_time)}s), "
                    f"respawning {len(remaining)} games with different proxy"
                )
                proc, fh = _respawn_worker(i, remaining, good_proxy, output_base)
                workers[i] = proc
                extra_log_handles.append(fh)
                respawned.add(i)
                worker_last_change[i] = time.time()

        # Update bar
        delta = games_done - prev_done
        if delta > 0:
            bar.update(delta)
            prev_done = games_done

        bar.set_postfix_str(
            f"{workers_done}/{num_workers} workers done, {errors} err"
        )

        if alive == 0:
            if games_done > prev_done:
                bar.update(games_done - prev_done)
            break

        time.sleep(5)

    bar.close()
    for fh in extra_log_handles:
        fh.close()

    # Check exit codes
    failures = []
    for i, w in enumerate(workers):
        if w.returncode != 0:
            failures.append(i)

    if failures:
        print(f"\n  WARNING: Workers {failures} exited with errors. Check logs/worker-*.log")
    else:
        print(f"\n  All {num_workers} workers completed successfully!")


# ---------------------------------------------------------------------------
# Worker process (runs inside subprocess)
# ---------------------------------------------------------------------------

def run_worker(worker_id: int, games_file: str, output_dir: str) -> None:
    """Worker process: collect box scores for assigned games.

    Reads game IDs from games_file, uses NBA_PROXY and NBA_REQUEST_DELAY
    from environment, writes to output_dir.
    """
    import pandas as pd

    from cuic_quant.data.nba.boxscores import (
        collect_advanced_boxscore,
        collect_hustle_boxscore,
        collect_tracking_boxscore,
        collect_traditional_boxscore,
    )
    from cuic_quant.data.nba.checkpoint import Checkpoint
    from cuic_quant.data.nba.constants import CSV_CONFIG
    from cuic_quant.data.nba.csv_writer import save_csv

    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s [W{worker_id}] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    proxy = os.environ.get("NBA_PROXY", "")
    delay = os.environ.get("NBA_REQUEST_DELAY", "1.0")
    logger.info("Worker %d starting: proxy=%s delay=%s", worker_id, proxy, delay)

    # Load game assignments
    games = json.loads(Path(games_file).read_text())
    logger.info("Worker %d: %d games to collect", worker_id, len(games))

    checkpoint = Checkpoint(output_path / ".nba_checkpoint.json")

    def _save(name: str, df: pd.DataFrame) -> None:
        if df.empty:
            return
        cfg = CSV_CONFIG[name]
        save_csv(df, output_path / cfg["file"], cfg["pk"])

    trad_player_frames: list[pd.DataFrame] = []
    trad_team_frames: list[pd.DataFrame] = []
    adv_frames: list[pd.DataFrame] = []
    hustle_frames: list[pd.DataFrame] = []
    tracking_frames: list[pd.DataFrame] = []
    games_processed = 0
    error_count = 0

    def _flush() -> None:
        if trad_player_frames:
            _save("nba_game_boxscores_player", pd.concat(trad_player_frames, ignore_index=True))
        if trad_team_frames:
            _save("nba_game_boxscores_team", pd.concat(trad_team_frames, ignore_index=True))
        if adv_frames:
            _save("nba_game_advanced_player", pd.concat(adv_frames, ignore_index=True))
        if hustle_frames:
            _save("nba_game_hustle_player", pd.concat(hustle_frames, ignore_index=True))
        if tracking_frames:
            _save("nba_game_tracking_player", pd.concat(tracking_frames, ignore_index=True))

    def _periods_for_game(num_ot: int) -> list[int]:
        periods = [0, 1, 2, 3, 4]
        for ot in range(1, num_ot + 1):
            periods.append(4 + ot)
        return periods

    start_time = time.monotonic()

    from concurrent.futures import ThreadPoolExecutor

    for game in games:
        game_id = game["game_id"]
        num_ot = game["num_ot"]

        # Skip if already collected (resume)
        if checkpoint.is_game_collected("boxscores", game_id):
            continue

        periods = _periods_for_game(num_ot)
        datasets_ok = []

        # Fire all 4 boxscore types in parallel (different endpoints, same proxy)
        with ThreadPoolExecutor(max_workers=4) as pool:
            trad_fut = pool.submit(collect_traditional_boxscore, game_id, periods=periods)
            adv_fut = pool.submit(collect_advanced_boxscore, game_id, periods=periods)
            hustle_fut = pool.submit(collect_hustle_boxscore, game_id)
            tracking_fut = pool.submit(collect_tracking_boxscore, game_id)

        # Gather results with independent error handling per type
        try:
            player_df, team_df = trad_fut.result()
            if not player_df.empty:
                trad_player_frames.append(player_df)
                datasets_ok.append("traditional_player")
            if not team_df.empty:
                trad_team_frames.append(team_df)
                datasets_ok.append("traditional_team")
        except Exception as e:
            checkpoint.add_error(f"{game_id}:traditional:{e}")
            error_count += 1

        try:
            adv_df = adv_fut.result()
            if not adv_df.empty:
                adv_frames.append(adv_df)
                datasets_ok.append("advanced")
        except Exception as e:
            checkpoint.add_error(f"{game_id}:advanced:{e}")
            error_count += 1

        try:
            hustle_df = hustle_fut.result()
            if not hustle_df.empty:
                hustle_frames.append(hustle_df)
                datasets_ok.append("hustle")
        except Exception as e:
            checkpoint.add_error(f"{game_id}:hustle:{e}")
            error_count += 1

        try:
            tracking_df = tracking_fut.result()
            if not tracking_df.empty:
                tracking_frames.append(tracking_df)
                datasets_ok.append("tracking")
        except Exception as e:
            checkpoint.add_error(f"{game_id}:tracking:{e}")
            error_count += 1

        checkpoint.mark_game_collected("boxscores", game_id)
        checkpoint.mark_game_datasets(game_id, datasets_ok)
        games_processed += 1

        # Flush periodically (every 5 games or 50, whichever is smaller)
        flush_interval = min(5, max(1, len(games) // 3))
        if games_processed % flush_interval == 0:
            _flush()
            trad_player_frames.clear()
            trad_team_frames.clear()
            adv_frames.clear()
            hustle_frames.clear()
            tracking_frames.clear()
            checkpoint.save()

            elapsed = time.monotonic() - start_time
            rate = games_processed / elapsed if elapsed > 0 else 0
            remaining = len(games) - games_processed
            eta_m = (remaining / rate / 60) if rate > 0 else 0
            logger.info(
                "Progress: %d/%d games (%.1f/sec, ETA %.0fm, %d errors)",
                games_processed, len(games), rate, eta_m, error_count,
            )

    # Final flush
    _flush()
    trad_player_frames.clear()
    trad_team_frames.clear()
    adv_frames.clear()
    hustle_frames.clear()
    tracking_frames.clear()
    checkpoint.save()

    elapsed_m = (time.monotonic() - start_time) / 60
    logger.info(
        "Worker %d DONE: %d games in %.1fm (%d errors)",
        worker_id, games_processed, elapsed_m, error_count,
    )


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_orchestrator(args: argparse.Namespace) -> None:
    """Main orchestrator: set up proxies, distribute work, monitor, cleanup."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    output_base = args.output_dir or "data"
    cleanup_needed = False
    using_proxy_file = bool(args.proxy_file)
    active_workers: list[subprocess.Popen] = []
    active_log_handles: list = []

    # Prevent macOS from sleeping during collection
    caffeinate_proc = subprocess.Popen(
        ["caffeinate", "-dims"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("  caffeinate: preventing sleep while collection runs")

    # Register cleanup on Ctrl-C
    def signal_handler(sig, frame):
        print("\n\n  Caught Ctrl-C! Cleaning up...")
        for w in active_workers:
            if w.poll() is None:
                w.terminate()
        for fh in active_log_handles:
            fh.close()
        caffeinate_proc.terminate()
        if cleanup_needed:
            destroy_droplets()
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Step 1: Get proxy URLs
        if using_proxy_file:
            print(f"\n--- Step 1: Loading proxies from {args.proxy_file} ---")
            proxy_urls = parse_proxy_file(args.proxy_file)
            if not proxy_urls:
                raise RuntimeError(f"No proxies found in {args.proxy_file}")
            print(f"  -> {len(proxy_urls)} proxies loaded")

            # Health check: drop bad proxies before starting
            proxy_urls = validate_proxies(proxy_urls)
            if not proxy_urls:
                raise RuntimeError("No working proxies found! Check network/VPN.")
            num_workers = min(len(proxy_urls), MAX_PARALLEL_WORKERS)
            print(f"  -> {len(proxy_urls)} healthy proxies, using {num_workers} workers")

        elif not args.skip_infra:
            num_workers = args.num_workers
            print(f"\n--- Step 1: Create proxy infrastructure ---")
            create_droplets(
                num=num_workers,
                size=args.droplet_size,
                region=args.region,
                ssh_key_id=args.ssh_key_id,
                image=args.image,
            )
            cleanup_needed = True
            droplets = wait_for_droplet_ips(num_workers)
            ports = open_ssh_tunnels(droplets)
            proxy_urls = [f"socks5h://127.0.0.1:{p}" for p in ports]

        else:
            num_workers = args.num_workers
            print(f"\n--- Step 1: Using existing tunnels (--skip-infra) ---")
            ports = list(range(BASE_SOCKS_PORT, BASE_SOCKS_PORT + num_workers))
            proxy_urls = [f"socks5h://127.0.0.1:{p}" for p in ports]
            print(f"  Assuming tunnels on ports {ports[0]}-{ports[-1]}")

        print(f"\n{'='*60}")
        print(f"  NBA Parallel Box Score Collection")
        print(f"  Workers: {num_workers}")
        print(f"  Proxy source: {'proxy file' if using_proxy_file else 'DigitalOcean'}")
        print(f"{'='*60}")

        # Step 2: Discover games (or load from existing CSV)
        print(f"\n--- Step 2: Discover games ---")
        if args.games_csv:
            import pandas as pd
            games_df = pd.read_csv(args.games_csv, dtype={"game_id": str})
            games = []
            for _, row in games_df.iterrows():
                games.append({
                    "game_id": row["game_id"],
                    "num_ot": int(row.get("num_ot") or 0),
                })
            print(f"  -> Loaded {len(games):,} games from {args.games_csv}")
        else:
            from cuic_quant.data.nba.api_helper import set_proxy_rotation
            set_proxy_rotation(proxy_urls)  # rotate all 100 proxies during discovery
            os.environ["NBA_REQUEST_DELAY"] = WORKER_REQUEST_DELAY  # 1.0s instead of 3.5s
            games = discover_all_games(args.seasons, output_dir=output_base)
            set_proxy_rotation([])  # disable rotation before workers launch
            os.environ.pop("NBA_REQUEST_DELAY", None)

        # Step 3: Distribute and launch
        print(f"\n--- Step 3: Launch {num_workers} workers ---")
        game_chunks = split_games(games, num_workers)
        actual_workers = len(game_chunks)

        print(f"  {len(games):,} games split into {actual_workers} chunks "
              f"(~{len(game_chunks[0])} games each)")

        workers, log_handles = launch_workers(
            num_workers=actual_workers,
            proxy_urls=proxy_urls,
            game_chunks=game_chunks,
            output_base=output_base,
        )
        active_workers = workers
        active_log_handles = log_handles

        # Step 4: Monitor
        print(f"\n--- Step 4: Monitoring ---")
        print(f"  Logs: tail -f logs/worker-*.log")
        monitor_workers(workers, output_base, total_games=len(games), proxy_urls=proxy_urls)

        # Close log file handles
        for fh in log_handles:
            fh.close()

        # Step 5: Summary
        print(f"\n--- Step 5: Summary ---")
        total_games = 0
        for i in range(actual_workers):
            worker_dir = Path(output_base) / f"worker-{i}"
            ckpt_path = worker_dir / ".nba_checkpoint.json"
            if ckpt_path.exists():
                ckpt = json.loads(ckpt_path.read_text())
                n = len(ckpt.get("games_collected", {}).get("boxscores", []))
                total_games += n

        print(f"  Total games collected: {total_games:,}")
        print(f"\n  Next step: python3 scripts/merge_nba_workers.py --cleanup")

    finally:
        caffeinate_proc.terminate()
        if cleanup_needed and not args.skip_infra:
            print(f"\n--- Cleanup ---")
            destroy_droplets()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parallel NBA box score collection via proxy rotation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Worker mode (internal, called by orchestrator)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--worker-id", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--games-file", help=argparse.SUPPRESS)

    # Proxy file (recommended)
    parser.add_argument(
        "--proxy-file",
        help="Path to proxy list file (webshare.io format: ip:port:user:pass)",
    )

    # Orchestrator args
    parser.add_argument(
        "--num-workers", type=int, default=50,
        help="Number of workers when using DO droplets (default: 50). "
             "Ignored with --proxy-file (uses all proxies in file).",
    )
    parser.add_argument(
        "--seasons", nargs="+", default=None,
        help="Seasons to collect (default: all)",
    )
    parser.add_argument(
        "--games-csv",
        help="Path to existing nba_games.csv to skip game discovery (much faster)",
    )
    parser.add_argument(
        "--output-dir", default="data",
        help="Base output directory (default: data)",
    )

    # DigitalOcean args (alternative to --proxy-file)
    do_group = parser.add_argument_group("DigitalOcean options (alternative to --proxy-file)")
    do_group.add_argument(
        "--ssh-key-id", default="",
        help="DO SSH key ID (from doctl compute ssh-key list)",
    )
    do_group.add_argument(
        "--droplet-size", default="s-1vcpu-512mb-10gb",
        help="DO droplet size (default: s-1vcpu-512mb-10gb)",
    )
    do_group.add_argument("--region", default="nyc1", help="DO region (default: nyc1)")
    do_group.add_argument("--image", default="ubuntu-24-04-x64", help="DO image")
    do_group.add_argument(
        "--skip-infra", action="store_true",
        help="Re-use existing SSH tunnels (skip droplet creation)",
    )

    args = parser.parse_args()

    if args.worker:
        run_worker(args.worker_id, args.games_file, args.output_dir)
    else:
        if not args.proxy_file and not args.skip_infra and not args.ssh_key_id:
            parser.error(
                "Provide --proxy-file (recommended) or --ssh-key-id (DO droplets)"
            )
        run_orchestrator(args)


if __name__ == "__main__":
    main()
