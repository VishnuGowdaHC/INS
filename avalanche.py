"""
Avalanche Effect Analysis & Cryptographic Metrics for Tiger-192.

The Avalanche Effect is a fundamental property of secure cryptographic hash functions
and block ciphers: when a single input bit changes (e.g. flipping 0 -> 1),
each output bit should flip with probability 0.5 (Strict Avalanche Criterion - SAC).
For Tiger-192, roughly 96 out of 192 output bits should invert.
"""

import math
import random
import statistics
from typing import Dict, Any, List, Union, Tuple
from tiger import tiger, tiger_hex, tiger_trace

# Known official test vectors for Tiger (Anderson & Biham)
TEST_VECTORS = {
    "": "3293ac630c13f0245f92bbb1766e16167a4e58492dde73f3",
    "a": "77befbef2e7ef8ab2ec8f93bf587a7fc613e247f5f247809",
    "abc": "2aab1484e8c158f2bfb8c5ff41b57a525129131c957b5f93",
    "message digest": "d981f8cb78201a950dcf3048751e441c517fca1aa55a29f6",
    "abcdefghijklmnopqrstuvwxyz": "1714a472eee57d30040412bfcc55032a0b11602ff37beee9",
    "The quick brown fox jumps over the lazy dog": "6d12a41e72e644f017b6f0e2f7b44c6285f06dd5d2c5b075",
}


def hamming_bits(d1: bytes, d2: bytes) -> int:
    """Calculates the number of differing bits (Hamming distance) between two byte strings."""
    return (int.from_bytes(d1, "big") ^ int.from_bytes(d2, "big")).bit_count()


def bytes_to_bits(d: bytes) -> str:
    """Converts a byte string to its zero-padded big-endian binary representation."""
    return bin(int.from_bytes(d, "big"))[2:].zfill(len(d) * 8)


def single_char_flip(msg: str, index: int) -> str:
    """Mutates a single character at the specified index."""
    if not msg:
        return "a"
    index = index % len(msg)
    old = msg[index]
    new = chr(ord(old) + 1) if old != "z" else "a"
    return msg[:index] + new + msg[index + 1:]


def single_bit_flip(data: bytes, bit_pos: int) -> bytes:
    """Inverts exactly one bit at `bit_pos` (0-indexed from MSB) in a byte string."""
    if not data:
        return b"\x01"
    ba = bytearray(data)
    byte_idx = (bit_pos // 8) % len(ba)
    bit_offset = 7 - (bit_pos % 8)
    ba[byte_idx] ^= (1 << bit_offset)
    return bytes(ba)


def analyze_avalanche(
    msg1: Union[str, bytes],
    msg2: Union[str, bytes]
) -> Dict[str, Any]:
    """
    Performs comprehensive avalanche analysis comparing two input messages.
    Calculates digests, Hamming distance, bitwise XOR matrix, and byte breakdowns.
    """
    b1 = msg1.encode("utf-8") if isinstance(msg1, str) else msg1
    b2 = msg2.encode("utf-8") if isinstance(msg2, str) else msg2

    h1 = tiger(b1)
    h2 = tiger(b2)

    total_bits = len(h1) * 8  # 192 bits
    xor_int = int.from_bytes(h1, "big") ^ int.from_bytes(h2, "big")
    xor_bits = bin(xor_int)[2:].zfill(total_bits)
    h1_bits = bytes_to_bits(h1)
    h2_bits = bytes_to_bits(h2)

    flipped_count = xor_int.bit_count()
    percentage = round((flipped_count / total_bits) * 100, 2)
    diff_indices = [i for i, ch in enumerate(xor_bits) if ch == "1"]

    # Byte-by-byte comparison
    bytes_breakdown = []
    for byte_idx in range(len(h1)):
        byte1_val = h1[byte_idx]
        byte2_val = h2[byte_idx]
        xor_val = byte1_val ^ byte2_val
        diff_bits = xor_val.bit_count()
        bytes_breakdown.append({
            "byte_index": byte_idx,
            "b1_hex": f"{byte1_val:02x}",
            "b2_hex": f"{byte2_val:02x}",
            "b1_bits": bin(byte1_val)[2:].zfill(8),
            "b2_bits": bin(byte2_val)[2:].zfill(8),
            "xor_bits": bin(xor_val)[2:].zfill(8),
            "flipped_bits": diff_bits
        })

    # Strict Avalanche Criterion (SAC) deviation: |percentage - 50%|
    sac_deviation = round(abs(percentage - 50.0), 2)
    sac_quality = "Optimal (~50%)" if sac_deviation < 5 else ("Good" if sac_deviation < 10 else "Moderate")

    return {
        "msg1": msg1 if isinstance(msg1, str) else b1.hex(),
        "msg2": msg2 if isinstance(msg2, str) else b2.hex(),
        "hash1_hex": h1.hex(),
        "hash2_hex": h2.hex(),
        "hash1_bits": h1_bits,
        "hash2_bits": h2_bits,
        "xor_bits": xor_bits,
        "diff_indices": diff_indices,
        "flipped_count": flipped_count,
        "total_bits": total_bits,
        "percentage": percentage,
        "ideal_count": 96,
        "ideal_percentage": 50.0,
        "sac_deviation": sac_deviation,
        "sac_quality": sac_quality,
        "bytes_breakdown": bytes_breakdown
    }


def analyze_pass_progression(msg1: str, msg2: str) -> List[Dict[str, Any]]:
    """
    Examines intermediate 192-bit states across Pass 1, Pass 2, and Pass 3
    to demonstrate how diffusion builds up through each round.
    """
    trace1 = tiger_trace(msg1)
    trace2 = tiger_trace(msg2)

    progression = []
    for step1, step2 in zip(trace1, trace2):
        d1 = step1["digest_bytes"]
        d2 = step2["digest_bytes"]
        diff = hamming_bits(d1, d2)
        pct = round((diff / 192) * 100, 2)
        xor_b = bin(int.from_bytes(d1, "big") ^ int.from_bytes(d2, "big"))[2:].zfill(192)

        progression.append({
            "stage": step1["stage"],
            "pass_number": step1["pass_number"],
            "multiplier": step1["multiplier"],
            "state1_hex": step1["digest_hex"],
            "state2_hex": step2["digest_hex"],
            "diff_bits": diff,
            "total_bits": 192,
            "percentage": pct,
            "xor_bits": xor_b
        })

    return progression


def run_statistical_simulation(
    base_msg: str = "The quick brown fox jumps over the lazy dog",
    num_trials: int = 500,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Runs a statistical Monte Carlo simulation evaluating single-bit flips
    to confirm adherence to the Strict Avalanche Criterion (Normal distribution around 96 bits).
    """
    rng = random.Random(seed)
    counts = []

    # 1. Deterministic character mutation trials
    for i in range(min(len(base_msg), 50)):
        m2 = single_char_flip(base_msg, i)
        counts.append(hamming_bits(tiger(base_msg.encode()), tiger(m2.encode())))

    # 2. Random 1-bit input flip trials
    base_bytes = base_msg.encode("utf-8")
    for _ in range(num_trials):
        # Choose a random byte and random bit
        byte_idx = rng.randrange(len(base_bytes))
        bit_idx = rng.randrange(8)
        mutated = bytearray(base_bytes)
        mutated[byte_idx] ^= (1 << bit_idx)

        diff = hamming_bits(tiger(base_bytes), tiger(bytes(mutated)))
        counts.append(diff)

    mean_val = round(statistics.mean(counts), 2)
    std_dev = round(statistics.pstdev(counts), 2)
    min_val = min(counts)
    max_val = max(counts)

    # Generate histogram data for visual graphing (bins from min to max)
    bin_min = max(60, min_val - 2)
    bin_max = min(132, max_val + 2)
    bins_dict = {b: 0 for b in range(bin_min, bin_max + 1)}
    for c in counts:
        if c in bins_dict:
            bins_dict[c] += 1

    histogram = [{"bits": b, "count": cnt} for b, cnt in sorted(bins_dict.items())]

    return {
        "trials_count": len(counts),
        "mean": mean_val,
        "stdev": std_dev,
        "min": min_val,
        "max": max_val,
        "expected_mean": 96.0,
        "expected_stdev": round(math.sqrt(192 * 0.5 * 0.5), 2),  # sqrt(npq) = sqrt(48) ~ 6.93
        "histogram": histogram
    }


def self_test() -> bool:
    """Verifies Tiger implementation against official reference test vectors."""
    for text, expected in TEST_VECTORS.items():
        computed = tiger_hex(text)
        if computed != expected:
            raise AssertionError(f"Tiger self-test failed for {text!r}: expected {expected}, got {computed}")
    return True
