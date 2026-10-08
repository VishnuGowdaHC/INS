"""
Tiger-192 Cryptographic Hash Function Implementation.
Designed by Ross Anderson and Eli Biham (1996) for fast 64-bit computing.

Produces a 192-bit (24-byte) message digest using 3 passes over 512-bit blocks.
"""

from typing import List, Tuple, Union, Dict, Any
from sboxes import T1, T2, T3, T4

# 64-bit integer mask
MASK = 0xFFFFFFFFFFFFFFFF

# Initial state (Initialization Vector / IV)
IV = (0x0123456789ABCDEF, 0xFEDCBA9876543210, 0xF096A5B4C3B2E187)


def _round(a: int, b: int, c: int, x: int, mul: int) -> Tuple[int, int, int]:
    """Single round step of the Tiger hash function."""
    c ^= x
    a = (a - (T1[c & 0xFF] ^ T2[(c >> 16) & 0xFF] ^ T3[(c >> 32) & 0xFF] ^ T4[(c >> 48) & 0xFF])) & MASK
    b = (b + (T4[(c >> 8) & 0xFF] ^ T3[(c >> 24) & 0xFF] ^ T2[(c >> 40) & 0xFF] ^ T1[(c >> 56) & 0xFF])) & MASK
    b = (b * mul) & MASK
    return a, b, c


def _pass(a: int, b: int, c: int, x: List[int], mul: int) -> Tuple[int, int, int]:
    """A full pass consisting of 8 sub-rounds with cyclical register shifts."""
    a, b, c = _round(a, b, c, x[0], mul)
    b, c, a = _round(b, c, a, x[1], mul)
    c, a, b = _round(c, a, b, x[2], mul)
    a, b, c = _round(a, b, c, x[3], mul)
    b, c, a = _round(b, c, a, x[4], mul)
    c, a, b = _round(c, a, b, x[5], mul)
    a, b, c = _round(a, b, c, x[6], mul)
    b, c, a = _round(b, c, a, x[7], mul)
    return a, b, c


def _key_schedule(x: List[int]) -> None:
    """Invertible key schedule mapping 8 64-bit words into next pass subkeys."""
    x[0] = (x[0] - (x[7] ^ 0xA5A5A5A5A5A5A5A5)) & MASK
    x[1] ^= x[0]
    x[2] = (x[2] + x[1]) & MASK
    x[3] = (x[3] - (x[2] ^ ((~x[1] & MASK) << 19 & MASK))) & MASK
    x[4] ^= x[3]
    x[5] = (x[5] + x[4]) & MASK
    x[6] = (x[6] - (x[5] ^ ((~x[4] & MASK) >> 23))) & MASK
    x[7] ^= x[6]
    x[0] = (x[0] + x[7]) & MASK
    x[1] = (x[1] - (x[0] ^ ((~x[7] & MASK) << 19 & MASK))) & MASK
    x[2] ^= x[1]
    x[3] = (x[3] + x[2]) & MASK
    x[4] = (x[4] - (x[3] ^ ((~x[2] & MASK) >> 23))) & MASK
    x[5] ^= x[4]
    x[6] = (x[6] + x[5]) & MASK
    x[7] = (x[7] - (x[6] ^ 0x0123456789ABCDEF)) & MASK


def pad_message(data: bytes) -> bytes:
    """Pad message according to Tiger specification (0x01 byte + zeros + 64-bit bit length)."""
    length = len(data)
    padded = bytearray(data)
    padded.append(0x01)
    # Pad with zeros until length is 56 mod 64
    pad_len = (56 - len(padded)) % 64
    padded.extend(b"\x00" * pad_len)
    # Append original bit length as 64-bit little endian integer
    bit_len = (length * 8) & MASK
    padded.extend(bit_len.to_bytes(8, "little"))
    return bytes(padded)


def _compress(block: bytes, state: List[int]) -> List[int]:
    """Compress a single 64-byte (512-bit) block into a 3-word state."""
    x = [int.from_bytes(block[i:i + 8], "little") for i in range(0, 64, 8)]
    a, b, c = state
    aa, bb, cc = a, b, c
    for pass_no, mul in enumerate((5, 7, 9)):
        if pass_no != 0:
            _key_schedule(x)
        a, b, c = _pass(a, b, c, x, mul)
        a, b, c = c, a, b  # cyclical register rotation
    a ^= aa
    b = (b - bb) & MASK
    c = (c + cc) & MASK
    return [a, b, c]


def tiger(data: Union[bytes, str]) -> bytes:
    """
    Computes the 24-byte (192-bit) Tiger digest of the given data.

    :param data: Input message as bytes or string
    :return: 24-byte raw digest
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    state = list(IV)
    padded = pad_message(data)

    for i in range(0, len(padded), 64):
        state = _compress(padded[i:i + 64], state)

    return b"".join(w.to_bytes(8, "little") for w in state)


def tiger_hex(data: Union[bytes, str]) -> str:
    """Computes the 48-character hexadecimal Tiger digest."""
    return tiger(data).hex()


def tiger_trace(data: Union[bytes, str]) -> List[Dict[str, Any]]:
    """
    Computes Tiger hash while capturing intermediate state after each pass
    for the final block. Useful for analyzing diffusion and avalanche progression.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    state = list(IV)
    padded = pad_message(data)
    num_blocks = len(padded) // 64

    # Process all but last block normally
    for i in range(0, (num_blocks - 1) * 64, 64):
        state = _compress(padded[i:i + 64], state)

    # Process last block while tracking passes
    last_block = padded[(num_blocks - 1) * 64:]
    x = [int.from_bytes(last_block[i:i + 8], "little") for i in range(0, 64, 8)]

    a, b, c = state
    aa, bb, cc = a, b, c
    pass_snapshots = []

    def state_to_bytes(sa: int, sb: int, sc: int) -> bytes:
        return b"".join(w.to_bytes(8, "little") for w in (sa, sb, sc))

    pass_snapshots.append({
        "stage": "Initial Block State",
        "pass_number": 0,
        "multiplier": 0,
        "state_words": [a, b, c],
        "digest_hex": state_to_bytes(a, b, c).hex(),
        "digest_bytes": state_to_bytes(a, b, c)
    })

    multipliers = (5, 7, 9)
    for pass_no, mul in enumerate(multipliers):
        if pass_no != 0:
            _key_schedule(x)
        a, b, c = _pass(a, b, c, x, mul)
        a, b, c = c, a, b

        pass_snapshots.append({
            "stage": f"After Pass {pass_no + 1} (mul={mul})",
            "pass_number": pass_no + 1,
            "multiplier": mul,
            "state_words": [a, b, c],
            "digest_hex": state_to_bytes(a, b, c).hex(),
            "digest_bytes": state_to_bytes(a, b, c)
        })

    # Feedforward combination
    a ^= aa
    b = (b - bb) & MASK
    c = (c + cc) & MASK

    final_bytes = state_to_bytes(a, b, c)
    pass_snapshots.append({
        "stage": "Final Digest (Feedforward Combined)",
        "pass_number": 4,
        "multiplier": None,
        "state_words": [a, b, c],
        "digest_hex": final_bytes.hex(),
        "digest_bytes": final_bytes
    })

    return pass_snapshots
