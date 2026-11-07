# PRIVATE_CLOUD — Multi-Account MEGA Cloud Storage Manager

## Overview

**PRIVATE_CLOUD** is a Python utility designed to manage file storage across multiple user-provided [MEGA](https://mega.nz/) accounts. It aggregates storage capacities across accounts, monitors available quota, splits oversized files into manageable chunks, reassembles split parts upon download, provides opt-in client-side AES-256-GCM encryption, and generates an interactive `output.html` to view and browse files.

> **Implementation Note:**
> - **Supported Provider:** MEGA is currently the **only supported cloud provider** (via `mega.py`). Support for additional providers (such as Google Drive) is a planned conceptual enhancement, not yet implemented.
> - **Account Registration:** This repository does **not** provide account creation automation. Users must provide their own legitimately registered MEGA credentials.
> - **Storage Scope:** This tool aggregates individual account quotas; it does **not** create "unlimited" storage out of thin air.

---

## 📦 Dependencies & Libraries Used

All dependencies are explicitly declared in `requirements.txt` to keep the architecture clean and interview-explainable:

### External Libraries (`requirements.txt`)
| Library | Version | Purpose & Interview Explanation |
| :--- | :--- | :--- |
| **`cryptography`** | `>=41.0.0` | Audited cryptographic primitives for client-side **AES-256-GCM** authenticated encryption and **Scrypt** password-based key derivation. |
| **`requests`** | `>=2.28.0` | High-performance streaming HTTP downloads for remote files directly to disk (with built-in `urllib` fallback). |
| **`mega.py`** | `>=1.0.8` | Python SDK used to communicate with the MEGA API (login, storage quota queries, file uploads, and public link retrieval). |

### Built-in Python Standard Libraries
- **`os` & `pathlib`**: File system navigation, path normalization, and file size detection.
- **`struct`**: Packs binary chunk lengths, 4-byte counters, and nonces for cryptographic packet framing.
- **`json`**: Secure parsing of `mega_credentials.json` account definitions.
- **`hashlib`**: Generates SHA-256 digests in unit tests to verify byte-for-byte integrity after file reassembly.
- **`unittest` & `tempfile`**: Built-in test runner and isolated test fixture creation without needing `pytest`.
- **`time` & `subprocess`**: Powers `WATCHDOG.py` by monitoring `os.path.getmtime` for file updates.

---

## Features & Implementation Status

| Feature | Status | Details |
|---|---|---|
| **MEGA Multi-Account Aggregation** | **Implemented** | Reads credentials from `mega_credentials.json`, checks available quota per account, selects account with sufficient space |
| **Large File Splitting** | **Implemented** | `split_large_file(file_path, chunk_size)` divides files > 19 GB into `.partN` files |
| **Streaming Reassembly** | **Implemented** | `join_parts(parts, output_path)` streams `.partN` files in numeric order with zero full-memory buffering |
| **Client-Side Encryption** | **Implemented** | `crypto/encrypt.py`: AES-256-GCM, 1 MiB chunked streaming, Scrypt key derivation, per-chunk authenticated nonces |
| **HTML File Viewer** | **Implemented** | `server_html_creater.py` builds browsable `output.html` from path maps so you can view all files and links in your browser |
| **Google Drive / Other Providers** | *Planned* | Conceptual roadmap item; no Google Drive code exists in this repository |

---

## Viewing & Browsing Your Files (`output.html`)

To view your files, folders, and cloud download links in an interactive web interface:
```bash
python server_html_creater.py
```
This generates `output.html` in the project directory. Double-click `output.html` or open it in any web browser to browse your folder hierarchy and click direct download links.

To automatically rebuild `output.html` whenever new files are uploaded:
```bash
python WATCHDOG.py
```

---

## Security & Client-Side Encryption

Client-side encryption is provided via the `crypto` package using standard primitives from the Python `cryptography` library:
- **Cipher:** AES-256-GCM (Authenticated Encryption with Associated Data).
- **Key Derivation:** Scrypt (`n=16384`, `r=8`, `p=1`) with a 16-byte cryptographically secure random salt stored in the file header.
- **Nonce Scheme:** 12-byte nonce per chunk composed of an 8-byte random prefix plus a 4-byte big-endian chunk counter.
- **Integrity Authentication:** Chunk sequence index is passed as Associated Authenticated Data (AAD) to prevent reordering or truncation.
- **Zero Disk Exposure:** The encryption passphrase and derived keys are held in memory only and never written to disk.

---

## Installation & Setup

### 1. Prerequisites
- Python 3.10+
- Install dependencies:
```bash
pip install -r requirements.txt
```

PowerShell:
```powershell
pip install -r requirements.txt
```

### 2. Configure Credentials
Copy the example credentials file and insert your personal MEGA account credentials:
```bash
cp mega_credentials.example.json mega_credentials.json
```
PowerShell:
```powershell
Copy-Item mega_credentials.example.json mega_credentials.json
```

Structure of `mega_credentials.json`:
```json
[
  {
    "email": "user@example.com",
    "password": "your_secure_password"
  }
]
```
*(Note: `mega_credentials.json` is ignored by `.gitignore` and must never be committed).*

---

## Usage

### Uploading Files or Folders
```bash
python FINAL_SINGLE_SERVER.py "path/to/local/file.zip" "target/remote/folder"
```

To encrypt the file client-side before uploading:
```bash
python FINAL_SINGLE_SERVER.py "path/to/local/file.zip" "target/remote/folder" --encrypt
```

### Reassembling Split Parts (--download)
To rejoin split `.partN` files into the original file:
```bash
python FINAL_SINGLE_SERVER.py --download "restored_file.iso" file.iso.part1 file.iso.part2 file.iso.part3
```

### Decrypting Encrypted Files (--decrypt)
```bash
python FINAL_SINGLE_SERVER.py --decrypt "file.zip.enc" "file.zip"
```

---

## Running Automated Tests

A dedicated test suite is included to verify splitting/reassembly and cryptographic integrity:
- `tests/test_split_join.py`: Generates a 5 MB random binary file, splits into 512 KB chunks, rejoins with `join_parts`, and asserts SHA-256 digest match.
- `tests/test_crypto.py`: Verifies round-trip encryption/decryption, wrong-passphrase rejection, and ciphertext tamper detection.

Run all tests:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

PowerShell:
```powershell
python -m unittest discover -s tests -p "test_*.py"
```

---

## Terms of Service & Security Disclaimer

This project is intended for educational purposes, personal storage backup, and architectural exploration. Users must comply with the terms of service of any cloud storage provider they interact with (including MEGA). Automated account generation, quota abuse, or storing unauthorized material is strictly against terms of service and may result in account termination.

---

## License
Distributed under the MIT License. Developed by Gochalam Vinod.
