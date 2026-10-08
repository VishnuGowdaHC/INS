"""
Tiger-192 Hash and Avalanche Effect Demonstration
Main Entry Point.

Usage:
  python main.py          # Runs CLI self-test and demo, then prompts to launch Web UI
  python main.py --cli    # Runs CLI demo and statistics only
  python main.py --web    # Starts the web server and opens browser
"""

import sys
import webbrowser
import threading
import time
from tiger import tiger, tiger_hex
import avalanche
import server


def self_test():
    print("[1/3] Self-Test:")
    try:
        avalanche.self_test()
        print("  [OK] Tiger implementation matches known test vectors\n")
    except AssertionError as e:
        print(f"  [FAIL] {e}\n")


def demo(msg1: str, index: int):
    print("[2/3] Avalanche Demo:")
    msg2 = avalanche.single_char_flip(msg1, index)
    res = avalanche.analyze_avalanche(msg1, msg2)

    print(f"  Message 1 : {msg1!r}")
    print(f"  Message 2 : {msg2!r}   (char at index {index}: {msg1[index]!r} -> {msg2[index]!r})\n")
    print(f"  Tiger(M1) : {res['hash1_hex']}")
    print(f"  Tiger(M2) : {res['hash2_hex']}")
    print(f"  Identical? : {res['hash1_hex'] == res['hash2_hex']}\n")
    print(f"  Binary M1 : {res['hash1_bits']}")
    print(f"  Binary M2 : {res['hash2_bits']}")
    print(f"  XOR       : {res['xor_bits']} (1 = bit differs)\n")
    print(f"  Differing bits: {res['flipped_count']} / {res['total_bits']}  ({res['percentage']}%)   ideal ~ 96 (50%)\n")


def statistics_run(msg1: str):
    print("[3/3] Statistics Run:")
    stats = avalanche.run_statistical_simulation(base_msg=msg1, num_trials=500)
    print(f"  Statistics over {stats['trials_count']} single-change trials:")
    print(f"    mean = {stats['mean']}  min = {stats['min']}  max = {stats['max']}  stdev = {stats['stdev']}")
    print("    (expected mean 96, stdev ~6.9)\n")


def launch_web(port: int = 8000, open_browser: bool = True):
    url = f"http://127.0.0.1:{port}"
    print(f"Starting web server at {url}")
    if open_browser:
        def open_tab():
            time.sleep(1.0)
            webbrowser.open(url)
        threading.Thread(target=open_tab, daemon=True).start()

    server.run_server(port=port)


def main():
    args = sys.argv[1:]
    port = 8000
    if "--port" in args:
        idx = args.index("--port")
        if idx + 1 < len(args) and args[idx + 1].isdigit():
            port = int(args[idx + 1])

    if "--web" in args or "-w" in args:
        launch_web(port=port, open_browser=True)
        return

    message = "The quick brown fox jumps over the lazy dog"
    self_test()
    demo(message, message.index("dog"))
    statistics_run(message)

    if "--cli" in args:
        return

    try:
        choice = input("Launch web frontend? [Y/n]: ").strip().lower()
        if choice in ("", "y", "yes"):
            launch_web(port=port, open_browser=True)
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")


if __name__ == "__main__":
    main()