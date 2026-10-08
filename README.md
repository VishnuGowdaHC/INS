# Tiger-192 Cryptographic Hash & Avalanche Effect Visualizer

An Information and Network Security (INS) project implementing the **Tiger-192** cryptographic hash function and providing an interactive analysis suite for the **Avalanche Effect** and the **Strict Avalanche Criterion (SAC)**.

> [!NOTE]
> **PDF Documentation**: A complete, publication-ready 7-page technical specification and workflow report is available in the repository: [`Tiger192_Workflow_and_Algorithm_Specification.pdf`](file:///e:/Projects/Projects/INS/Tiger192_Workflow_and_Algorithm_Specification.pdf).

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [What Exactly Is It?](#what-exactly-is-it)
3. [Core Cryptographic Concepts](#core-cryptographic-concepts)
   - [Tiger-192 Hash Function](#tiger-192-hash-function)
   - [The Avalanche Effect](#the-avalanche-effect)
   - [Strict Avalanche Criterion (SAC)](#strict-avalanche-criterion-sac)
4. [Step-by-Step Working Mechanism](#step-by-step-working-mechanism)
   - [Phase 1: Message Padding](#phase-1-message-padding)
   - [Phase 2: Block Decomposition](#phase-2-block-decomposition)
   - [Phase 3: State Initialization](#phase-3-state-initialization)
   - [Phase 4: Round Compression & S-Box Substitution](#phase-4-round-compression--s-box-substitution)
   - [Phase 5: Key Schedule (Subkey Generation)](#phase-5-key-schedule-subkey-generation)
   - [Phase 6: Feedforward Combination](#phase-6-feedforward-combination)
   - [Phase 7: Final Digest Assembly](#phase-7-final-digest-assembly)
   - [Phase 8: Avalanche Metric Computation](#phase-8-avalanche-metric-computation)
5. [Step-by-Step Example Walkthrough](#step-by-step-example-walkthrough)
6. [Where It Is Used (Applications)](#where-it-is-used-applications)
7. [Technology Stack](#technology-stack)
8. [How to Give Inputs](#how-to-give-inputs)
   - [1. Web Graphical User Interface](#1-web-graphical-user-interface)
   - [2. Command-Line Interface (CLI)](#2-command-line-interface-cli)
   - [3. HTTP REST API](#3-http-rest-api)
   - [4. Python Module Import](#4-python-module-import)
9. [Project File Structure](#project-file-structure)
10. [Reference Test Vectors](#reference-test-vectors)
11. [Quick Start & Execution](#quick-start--execution)

---

## Project Overview

In cryptography, two pillars of security defined by Claude Shannon are **Confusion** (obscuring the relationship between the plaintext and the ciphertext/hash) and **Diffusion** (spreading the influence of each individual plaintext bit over the entire output).

This project implements:
1. A pure reference implementation of the **Tiger-192** cryptographic hash function (designed in 1996 by Ross Anderson and Eli Biham) in both **Python** and **client-side JavaScript**.
2. An analytical engine measuring the **Avalanche Effect**: the principle that flipping even a single bit in the input message should cause approximately half (~50%) of the output bits to flip independently and unpredictably.
3. A visualizer featuring:
   - Real-time side-by-side hash comparison.
   - Hamming distance calculation.
   - 192-cell interactive difference matrix with bit-level inspection.
   - Monte Carlo statistical simulation (testing SAC across hundreds of randomized single-bit and single-character mutations).
   - Built-in validation suite against official Anderson & Biham test vectors.

---

## What Exactly Is It?

This project is a **dual-engine cryptographic simulation and analysis platform**:

- **Cryptographic Hash Engine**: Implements Tiger-192 from scratch. Tiger-192 processes data in 512-bit (64-byte) blocks and produces a 192-bit (24-byte, 48-hexadecimal-character) message digest. It was specifically engineered for high performance on 64-bit processors, making heavy use of 64-bit registers, arithmetic additions, subtractions, multiplications, bitwise XORs, and four precomputed $256 \times 64$-bit substitution boxes ($S$-boxes / $T$-tables).
- **Avalanche Visualizer**: A complete web interface allowing users to type two messages, flip characters or individual bits with one click, and see immediate visual feedback on bit flips, XOR differences, and SAC compliance.
- **Statistical Testing Suite**: Evaluates the Strict Avalanche Criterion over $N$ random mutations, plotting empirical mean ($\mu$) and standard deviation ($\sigma$) against theoretical binomial expectations.

---

## Core Cryptographic Concepts

### Tiger-192 Hash Function

Designed by Ross Anderson and Eli Biham in 1996, Tiger was created as an alternative to MD5 and SHA-1 that was faster on 64-bit architectures (such as DEC Alpha). Key characteristics:
- **Digest Size**: 192 bits (24 bytes). Also variants Tiger-128 and Tiger-160 truncate this digest.
- **Block Size**: 512 bits (64 bytes).
- **Word Size**: 64 bits (eight 64-bit words per block: $x_0, x_1, \dots, x_7$).
- **Structure**: 3 passes per block, each pass comprising 8 sub-rounds (total of 24 sub-rounds per block).
- **Internal State**: Three 64-bit registers: $a$, $b$, and $c$.

### The Avalanche Effect

The **Avalanche Effect** (first coined by Horst Feistel) states that a small change in the input (such as flipping a single bit) must cause a significant, unpredictable change in the output (resembling an avalanche). Without this property:
- Attackers could correlate small input differences to small output differences.
- Differential cryptanalysis could be used to find collisions or invert the hash.

### Strict Avalanche Criterion (SAC)

Formulated by Webster and Tavares in 1985, the **Strict Avalanche Criterion (SAC)** formalizes the avalanche effect:

> *A cryptographic function satisfies SAC if, whenever a single input bit is complemented, each output bit changes with a probability of exactly 0.5.*

For a 192-bit hash:
- **Expected Differing Bits ($\mu$)**:
  $$\mu = n \cdot p = 192 \times 0.5 = 96 \text{ bits}$$
- **Theoretical Variance ($\sigma^2$)**:
  $$\sigma^2 = n \cdot p \cdot (1 - p) = 192 \times 0.5 \times 0.5 = 48$$
- **Theoretical Standard Deviation ($\sigma$)**:
  $$\sigma = \sqrt{48} \approx 6.928 \text{ bits}$$

In this project, statistical simulations run repeated single-bit mutations to verify that the empirical distribution closely follows $B(192, 0.5) \approx \mathcal{N}(96, 6.93)$.

---

## Step-by-Step Working Mechanism

The Tiger-192 algorithm executes through the following distinct stages:

```
+-----------------------------------------------------------+
|                      Input Message                        |
+-----------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------+
| Phase 1: Padding (Append 0x01, Zeroes, 64-bit Bit Length) |
+-----------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------+
| Phase 2: Split into 512-bit Blocks (x[0] ... x[7])        |
+-----------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------+
| Phase 3: Initialize State Registers (a, b, c) with IV     |
+-----------------------------------------------------------+
                              |
               +--------------+--------------+
               | For each 512-bit block:     |
               v                             |
+------------------------------------------+ |
| Pass 1: 8 Sub-rounds (multiplier = 5)    | |
|         S-box Lookups (T1, T2, T3, T4)   | |
+------------------------------------------+ |
               |                             |
               v                             |
+------------------------------------------+ |
| Key Schedule 1: Invertible Mix of x[0..7]| |
+------------------------------------------+ |
               |                             |
               v                             |
+------------------------------------------+ |
| Pass 2: 8 Sub-rounds (multiplier = 7)    | |
|         S-box Lookups (T1, T2, T3, T4)   | |
+------------------------------------------+ |
               |                             |
               v                             |
+------------------------------------------+ |
| Key Schedule 2: Second Mix of x[0..7]    | |
+------------------------------------------+ |
               |                             |
               v                             |
+------------------------------------------+ |
| Pass 3: 8 Sub-rounds (multiplier = 9)    | |
|         S-box Lookups (T1, T2, T3, T4)   | |
+------------------------------------------+ |
               |                             |
               v                             |
+------------------------------------------+ |
| Feedforward: a ^= a0, b -= b0, c += c0   | |
+------------------------------------------+ |
               +--------------+--------------+
                              |
                              v
+-----------------------------------------------------------+
| Phase 7: Export State (a, b, c) as 24 Bytes (Little Endian)|
+-----------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------+
| Phase 8: Avalanche XOR & Hamming Distance vs Mutant       |
+-----------------------------------------------------------+
```

### Phase 1: Message Padding
To ensure the input message is a multiple of 64 bytes (512 bits) and resists length-extension attacks:
1. Append the single byte `0x01` (`0b00000001`).
2. Append `0x00` bytes until the message length is congruent to $56 \pmod{64}$ (i.e., exactly 8 bytes short of a 64-byte boundary).
3. Append the original message length in bits as a 64-bit (8-byte) unsigned integer in **little-endian** format.

### Phase 2: Block Decomposition
The padded message is partitioned into consecutive 64-byte blocks. Each 64-byte block is read as eight 64-bit unsigned integers:
$$x = [x_0, x_1, x_2, x_3, x_4, x_5, x_6, x_7]$$
Each word is converted using little-endian byte ordering.

### Phase 3: State Initialization
The internal state comprises three 64-bit words: $a, b, c$. For the initial block, they are loaded with the Initialization Vector (IV):
- $a = \text{0x0123456789ABCDEF}$
- $b = \text{0xFEDCBA9876543210}$
- $c = \text{0xF096A5B4C3B2E187}$

### Phase 4: Round Compression & S-Box Substitution
Each block is processed through three passes. Each pass consists of 8 sub-rounds corresponding to words $x_0 \dots x_7$.

Within a sub-round `_round(a, b, c, x[i], mul)`:
1. XOR subkey word into $c$:
   $$c \leftarrow c \oplus x[i]$$
2. Extract the 8 bytes of $c$: $(c_0, c_1, c_2, c_3, c_4, c_5, c_6, c_7)$.
3. Update $a$ using four S-box lookups on even-indexed bytes:
   $$a \leftarrow \left(a - (T_1[c_0] \oplus T_2[c_2] \oplus T_3[c_4] \oplus T_4[c_6])\right) \pmod{2^{64}}$$
4. Update $b$ using four S-box lookups on odd-indexed bytes:
   $$b \leftarrow \left(b + (T_4[c_1] \oplus T_3[c_3] \oplus T_2[c_5] \oplus T_1[c_7])\right) \pmod{2^{64}}$$
5. Multiply $b$ by the pass multiplier:
   $$b \leftarrow (b \times \text{mul}) \pmod{2^{64}}$$
   - In Pass 1: $\text{mul} = 5$
   - In Pass 2: $\text{mul} = 7$
   - In Pass 3: $\text{mul} = 9$

After each sub-round, the registers rotate cyclically: $(a, b, c) \to (b, c, a) \to (c, a, b)$. After 8 sub-rounds, a final register rotation $(c, a, b)$ restores alignment.

### Phase 5: Key Schedule (Subkey Generation)
Between passes, the 8 words $x[0 \dots 7]$ undergo an invertible linear/non-linear mixing transformation to guarantee that every input bit influences subsequent passes differently:

**Key Schedule 1 (between Pass 1 and Pass 2):**
- Uses constant `0xA5A5A5A5A5A5A5A5`
- Mixes words sequentially:
  $$x_0 = (x_0 - (x_7 \oplus \text{0xA5A5A5A5A5A5A5A5})) \pmod{2^{64}}$$
  $$x_1 = x_1 \oplus x_0$$
  $$x_2 = (x_2 + x_1) \pmod{2^{64}}$$
  $$x_3 = \left(x_3 - \left(x_2 \oplus ((\sim x_1) \ll 19)\right)\right) \pmod{2^{64}}$$
  $$x_4 = x_4 \oplus x_3$$
  $$x_5 = (x_5 + x_4) \pmod{2^{64}}$$
  $$x_6 = \left(x_6 - \left(x_5 \oplus ((\sim x_4) \gg 23)\right)\right) \pmod{2^{64}}$$
  $$x_7 = x_7 \oplus x_6$$
  (Followed by a second cascade ending with XOR constant `0x0123456789ABCDEF`).

### Phase 6: Feedforward Combination
After Pass 3 completes for a block, the state is combined with its initial value before that block began (Davies-Meyer / Miyaguchi-Preneel construction):
$$a \leftarrow a \oplus a_{\text{initial}}$$
$$b \leftarrow (b - b_{\text{initial}}) \pmod{2^{64}}$$
$$c \leftarrow (c + c_{\text{initial}}) \pmod{2^{64}}$$

### Phase 7: Final Digest Assembly
When all 64-byte blocks are processed, the final state $(a, b, c)$ is serialized:
- $a$ encoded into 8 bytes (little-endian)
- $b$ encoded into 8 bytes (little-endian)
- $c$ encoded into 8 bytes (little-endian)

Total output: $8 + 8 + 8 = 24$ bytes ($192$ bits), displayed as a 48-character hexadecimal string.

### Phase 8: Avalanche Metric Computation
Given two messages $M_1$ and $M_2$:
1. Compute $H_1 = \text{Tiger}(M_1)$ and $H_2 = \text{Tiger}(M_2)$.
2. Compute the bitwise XOR difference:
   $$\Delta = H_1 \oplus H_2$$
3. Compute the **Hamming Distance** (differing bit count):
   $$d_H = \text{popcount}(\Delta)$$
4. Calculate the avalanche percentage:
   $$\text{Avalanche \%} = \frac{d_H}{192} \times 100\%$$
5. Compute SAC deviation:
   $$\text{Deviation} = |\text{Avalanche \%} - 50.00\%|$$

---

## Step-by-Step Example Walkthrough

Consider two messages that differ by exactly **one character** (and only **one bit** in that character):

- **Message 1 ($M_1$)**: `"The quick brown fox jumps over the lazy dog"`
- **Message 2 ($M_2$)**: `"The quick brown fox jumps over the lazy eog"`

### Input Difference Analysis
- At index 40, `'d'` is changed to `'e'`.
- ASCII of `'d'`: `0x64` = binary `01100100`
- ASCII of `'e'`: `0x65` = binary `01100101`
- Difference: Exactly **1 bit** flipped in the input message ($0 \to 1$).

### Execution Trace

1. **Length Calculation**:
   - Both messages are 43 characters long (344 bits).
2. **Padding**:
   - Append `0x01`.
   - Pad with 12 zero bytes (`0x00`) to reach 56 bytes.
   - Append 8-byte bit length: `344` as `0x5801000000000000`.
   - Result: Exactly one 64-byte (512-bit) block.
3. **Pass Execution**:
   - Pass 1 runs with multiplier 5.
   - Key schedule transforms words $x_0 \dots x_7$.
   - Pass 2 runs with multiplier 7.
   - Key schedule transforms words again.
   - Pass 3 runs with multiplier 9.
   - Feedforward combines final state with $(a_0, b_0, c_0)$.
4. **Resulting Tiger-192 Hashes**:
   - $\text{Tiger}(M_1) = \text{6d12a41e72e644f017b6f0e2f7b44c6285f06dd5d2c5b075}$
   - $\text{Tiger}(M_2) = \text{0b57bcbbd81a0d806c4441873c43e749034c758996141100}$
5. **Binary Representations (192 bits)**:
   - $M_1$: `011011010001001010100100000111100111001011100110010001001111000000010111101101101111000011100010111101111011010001001100011000101000010111110000011011011101010111010010110001011011000001110101`
   - $M_2$: `000010110101011110111100101110111101100000011010000011011000000001101100010001000100000110000111001111000100001111100111010010010000001101001100011101011000100110010110000101000001000100000000`
6. **XOR Difference Stream**:
   - `011001100100010100011000101001011010101011111100010010010111000001111011111100101011000101100101110010111111011110101011001010111000011010111100000110000101110001000100110100011010000101110101`
7. **Avalanche Measurement**:
   - Total Bits: **192**
   - Differing Bits (1s in XOR): **97 bits**
   - Percentage: **50.52%** (virtually identical to the theoretical ideal of **50.00% / 96 bits**)
   - SAC Deviation: **|50.52% - 50.00%| = 0.52%** (Optimal)

---

## Where It Is Used (Applications)

While SHA-2 and SHA-3 dominate TLS certificates and modern web standards today, Tiger-192 and the Avalanche principles demonstrated here are utilized in several major areas:

1. **Peer-to-Peer Networks & File Sharing (TTH - Tiger Tree Hash)**:
   - Direct Connect (NMDC / ADC) protocols utilize Tiger Tree Hashes (TTH) as the core content-addressable identifier.
   - Gnutella2 and Shareaza use TTH for decentralized file integrity verification and segment-level corruption repair via Merkle trees.
2. **Merkle Trees & Block Verification**:
   - Because Tiger-192 produces a 192-bit digest (smaller than SHA-256 while maintaining strong diffusion), it reduces tree storage overhead in high-throughput distributed systems.
3. **Information and Network Security (INS) Education**:
   - Demonstrating the core mechanics of block ciphers and hash functions: S-box lookups, Feistel/Davies-Meyer structures, confusion, diffusion, and SAC.
4. **Data Integrity & Forensic Checksums**:
   - Used in file verification tools (such as RHash, HashCheck) for fast multi-algorithm data validation.
5. **Cryptographic Benchmarking**:
   - Historical and modern benchmark for analyzing how 64-bit word operations compare against 32-bit algorithms (MD5, SHA-1).

---

## Technology Stack

| Layer | Component | Description |
|---|---|---|
| **Backend / Core Engine** | Python 3.8+ | Zero external pip dependencies. Uses Python standard library (`http.server`, `statistics`, `threading`, `webbrowser`, `urllib.parse`, `typing`). |
| **Hash Algorithm (Backend)** | `tiger.py`, `sboxes.py` | Pure Python bitwise implementation of Tiger-192, including 1024 64-bit S-box constants ($T_1, T_2, T_3, T_4$). |
| **Statistical Engine** | `avalanche.py` | Hamming distance, single-bit and single-char mutation generators, Monte Carlo distribution testing, and reference vector verification. |
| **Web Server & API** | `server.py` | Multi-threaded HTTP server (`ThreadingHTTPServer`) with CORS headers, JSON REST API, and static file hosting. |
| **Frontend UI** | HTML5 / Vanilla CSS3 | High-contrast, minimalist design system (dark/light, glass cards, 100vh viewport fit, no external CSS frameworks). |
| **Client-Side Engine** | `frontend/js/tiger.js` | 100% pure client-side JavaScript Tiger-192 engine using native `BigInt` and `BigUint64Array`. Zero latency, works offline. |
| **UI Controller** | `frontend/js/app.js` | Live real-time calculations, tab navigation, copy-to-clipboard, interactive 192-bit matrix inspector, and dynamic DOM rendering. |

---

## How to Give Inputs

There are four ways to interact with the project and provide inputs:

### 1. Web Graphical User Interface

Start the web application:
```bash
python main.py --web
```
Or:
```bash
python server.py
```
Open **http://localhost:8000** in your browser.

#### Available Controls:
- **Direct Typing**: Type or paste any text into the **Message 1 (Original)** and **Message 2 (Modified)** textareas. The cryptographic engine recalculates the hash, bit counts, progress bar, and matrix live on every keystroke.
- **Change 1 Character**: Mutates a single character in Message 2 to immediately see single-character avalanche.
- **Flip 1 Bit**: Inverts exactly one binary bit in Message 2.
- **Clone Message 1**: Copies Message 1 into Message 2 (shows 0% avalanche / 0 flipped bits).
- **Reset Default**: Restores default test messages.
- **Interactive 192-Bit Matrix**: Hover or click on any of the 192 cells in the matrix to inspect:
  - Bit index (`#0` to `#191`)
  - Byte index (`#0` to `#23`)
  - Value in Message 1 (`0` or `1`)
  - Value in Message 2 (`0` or `1`)
  - Match status (Matching vs Differing)
- **Statistical Simulation Tab**: Enter trial count (50 to 1000) and click **Run Statistical Test** to execute randomized bit-flip experiments with real-time statistics ($\mu$, $\sigma$, min, max).
- **Self-Test Vectors Tab**: Click **Verify All Test Vectors** to execute and validate Anderson & Biham standard reference tests.

---

### 2. Command-Line Interface (CLI)

Run through the command line using `main.py`:

```bash
# Full automated run (Self-test -> Single-char demo -> 500-trial Monte Carlo -> Web prompt)
python main.py

# CLI only (Runs self-test, avalanche demo, and statistical test, then exits)
python main.py --cli

# Direct web launcher
python main.py --web

# Custom web server port
python main.py --web --port 8080
```

#### Sample Terminal Output:
```text
[1/3] Self-Test:
  [OK] Tiger implementation matches known test vectors

[2/3] Avalanche Demo:
  Message 1 : 'The quick brown fox jumps over the lazy dog'
  Message 2 : 'The quick brown fox jumps over the lazy eog'   (char at index 40: 'd' -> 'e')

  Tiger(M1) : 6d12a41e72e644f017b6f0e2f7b44c6285f06dd5d2c5b075
  Tiger(M2) : 0b57bcbbd81a0d806c4441873c43e749034c758996141100
  Identical? : False

  Binary M1 : 011011010001001010100100...
  Binary M2 : 000010110101011110111100...
  XOR       : 011001100100010100011000... (1 = bit differs)

  Differing bits: 97 / 192  (50.52%)   ideal ~ 96 (50%)

[3/3] Statistics Run:
  Statistics over 543 single-change trials:
    mean = 97.07  min = 77  max = 116  stdev = 6.8
    (expected mean 96, stdev ~6.9)
```

---

### 3. HTTP REST API

The built-in HTTP server provides REST endpoints returning standard JSON. You can test them using `curl`, Postman, or any programming language:

#### A. Hash a String
```bash
curl -X POST http://localhost:8000/api/hash \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World"}'
```
**Response:**
```json
{
  "text": "Hello World",
  "hex": "5f6f4fa75231c50e41f71dfac8fae19a4e8d3810ec54cfcb",
  "bits": "010111110110111101001111...",
  "total_bits": 192,
  "bytes_length": 24
}
```

#### B. Compare Two Messages for Avalanche
```bash
curl -X POST http://localhost:8000/api/avalanche \
  -H "Content-Type: application/json" \
  -d '{
    "msg1": "Hello World",
    "msg2": "Hello world"
  }'
```
**Response:**
```json
{
  "hash1_hex": "5f6f4fa75231c50e41f71dfac8fae19a4e8d3810ec54cfcb",
  "hash2_hex": "b59d99f0bce4fe10a56885dfda20942ff655f4eb270a4a03",
  "flipped_count": 92,
  "total_bits": 192,
  "percentage": 47.92,
  "ideal_count": 96,
  "sac_deviation": 2.08,
  "sac_quality": "Optimal (~50%)"
}
```

#### C. Run Monte Carlo Statistical Simulation
```bash
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Information and Network Security",
    "trials": 300
  }'
```

#### D. Verify Reference Test Vectors
```bash
curl -X GET http://localhost:8000/api/test-vectors
```

#### E. Health Check
```bash
curl -X GET http://localhost:8000/api/health
```

---

### 4. Python Module Import

You can directly import the core modules into your own Python scripts:

```python
from tiger import tiger, tiger_hex
from avalanche import analyze_avalanche, run_statistical_simulation

# 1. Compute a 192-bit Tiger hash
digest = tiger_hex("Cryptographic Hash")
print("Tiger Hex:", digest)

# 2. Analyze avalanche effect between two messages
results = analyze_avalanche("Message Alpha", "Message Beta")
print(f"Flipped Bits: {results['flipped_count']} / {results['total_bits']} ({results['percentage']}%)")

# 3. Run Monte Carlo simulation
stats = run_statistical_simulation("Base message text", num_trials=200)
print(f"Mean: {stats['mean']}, StdDev: {stats['stdev']}")
```

---

## Project File Structure

```
INS/
├── Tiger192_Workflow_and_Algorithm_Specification.pdf # Publication-ready 7-page PDF specification
├── Tiger192_Documentation.html                       # HTML source for PDF generation with embedded SVG diagrams
├── sboxes.py            # Precomputed Tiger-192 S-Box substitution tables (T1, T2, T3, T4 - 1024 64-bit words)
├── tiger.py             # Pure Python cryptographic hash implementation (Padding, Passes, Key Schedule, Round logic)
├── avalanche.py         # Hamming distance calculator, single-bit/char mutations, Monte Carlo statistical analysis
├── server.py            # Multi-threaded HTTP server (API endpoints + static frontend host, zero dependencies)
├── main.py              # CLI runner, automated self-test, demo runner, and web server launcher
├── requirements.txt     # Environment requirements (Python >= 3.8, standard library only)
├── README.md            # Complete project documentation and reference
└── frontend/            # Web interface (Minimalist, accessible, responsive design)
    ├── index.html       # Single-page web application with tabbed interface
    ├── css/
    │   └── style.css    # High-contrast CSS layout, dark/light styling, grid and progress bars
    └── js/
        ├── tiger.js     # Standalone client-side Tiger-192 engine (Native BigInt and BigUint64Array)
        └── app.js       # Live event handlers, 192-bit interactive difference matrix, test vector runner
```

---

## Reference Test Vectors

The implementation is verified against the official test vectors published by Ross Anderson and Eli Biham:

| Input Message | Expected Tiger-192 Hexadecimal Digest | Status |
|---|---|:---:|
| `""` (Empty string) | `3293ac630c13f0245f92bbb1766e16167a4e58492dde73f3` | Verified |
| `"a"` | `77befbef2e7ef8ab2ec8f93bf587a7fc613e247f5f247809` | Verified |
| `"abc"` | `2aab1484e8c158f2bfb8c5ff41b57a525129131c957b5f93` | Verified |
| `"message digest"` | `d981f8cb78201a950dcf3048751e441c517fca1aa55a29f6` | Verified |
| `"abcdefghijklmnopqrstuvwxyz"` | `1714a472eee57d30040412bfcc55032a0b11602ff37beee9` | Verified |
| `"The quick brown fox jumps over the lazy dog"` | `6d12a41e72e644f017b6f0e2f7b44c6285f06dd5d2c5b075` | Verified |

---

## Quick Start & Execution

### Prerequisites
- Python 3.8 or higher.
- No external libraries required (`pip install` is not needed).
- Any modern web browser (Chrome, Edge, Firefox, Safari).

### Run in 1 Command
```bash
python main.py
```
This runs the internal self-test, prints an avalanche demonstration, runs a 500-trial statistical simulation, and offers to launch the interactive web visualizer.
