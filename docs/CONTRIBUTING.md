# Aegis – Contributing Guide

> **Version:** 1.0.0  
> **Last Updated:** 2026-05-13  

---

## Table of Contents

- [1. Welcome](#1-welcome)
- [2. Development Setup](#2-development-setup)
- [3. Code Style](#3-code-style)
- [4. Project Conventions](#4-project-conventions)
- [5. Git Workflow](#5-git-workflow)
- [6. Pull Request Process](#6-pull-request-process)
- [7. Testing Guidelines](#7-testing-guidelines)
- [8. Security Vulnerability Reporting](#8-security-vulnerability-reporting)
- [9. Architecture Rules](#9-architecture-rules)

---

## 1. Welcome

Thank you for considering contributing to Aegis! This guide will help you get started with the development workflow, code standards, and contribution process.

**Before you start:**
- Read the [Architecture Guide](ARCHITECTURE.md) to understand the system design
- Read the [Security Specification](SECURITY.md) to understand the cryptographic protocol
- Check existing issues and PRs to avoid duplicate work

---

## 2. Development Setup

```bash
# Clone the repository
git clone https://github.com/your-username/aegis-messenger.git
cd aegis-messenger

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov flake8 mypy black isort

# Verify setup
python -c "from core.crypto_engine import generate_rsa_keypair; print('✓ Ready')"

# Run the desktop app
python main_desktop.py
```

---

## 3. Code Style

### Python Standards

| Rule | Standard | Tool |
|------|----------|------|
| Formatting | PEP 8, max line length 99 | `black --line-length 99` |
| Import ordering | stdlib → third-party → local | `isort` |
| Type hints | Required on all public functions | `mypy --strict` |
| Docstrings | NumPy-style | Manual review |
| Naming | `snake_case` for functions/variables, `PascalCase` for classes | `flake8` |

### Type Hints (Mandatory)

Every public function must have complete type annotations:

```python
# ✅ Good
def encrypt_message(
    plaintext: str,
    recipient_public_keys: List[RSAPublicKey],
) -> Dict[str, Any]:
    """Encrypt a text message for one or more recipients."""
    ...

# ❌ Bad
def encrypt_message(plaintext, keys):
    ...
```

### Docstrings (NumPy Style)

```python
def aes_encrypt(plaintext: bytes) -> Tuple[bytes, bytes, bytes]:
    """Encrypt plaintext with a fresh AES-256-GCM key and nonce.

    Parameters
    ----------
    plaintext : bytes
        Raw data to encrypt.

    Returns
    -------
    Tuple[bytes, bytes, bytes]
        ``(aes_key, nonce, ciphertext_with_tag)``

    Raises
    ------
    ValueError
        If plaintext is empty.
    """
```

### Formatting Commands

```bash
# Format code
black --line-length 99 .

# Sort imports
isort .

# Lint
flake8 --max-line-length 99 --exclude .venv,dist,build

# Type check
mypy core/ --ignore-missing-imports
```

---

## 4. Project Conventions

### File Organization

| Directory | Content | Rules |
|-----------|---------|-------|
| `core/` | Business logic | No UI imports. No Kivy imports. |
| `ui/desktop/` | Desktop screens | Import from `core/` and `ui/shared/`. Never from `ui/mobile/`. |
| `ui/mobile/` | Mobile screens | Import from `core/` and `ui/shared/`. Never from `ui/desktop/`. |
| `ui/shared/` | Reusable widgets | Import from Kivy/KivyMD only. Never from `ui/desktop/` or `ui/mobile/`. |

### Threading Rules

1. **Never** call `requests.*` or `crypto_engine.*` from the main Kivy thread
2. Use `threading.Thread(target=..., daemon=True).start()` for background work
3. Use `Clock.schedule_once(callback, 0)` to update UI from background threads
4. All background threads must be daemon threads (auto-killed on app exit)

### Colour Constants

Use the colour constants from `ui/shared/widgets.py` — never hardcode hex values:

```python
from ui.shared.widgets import ACCENT_CYAN, BG_PRIMARY, TEXT_PRIMARY
```

### KV Language Rules

- All KV widget rules go inside `Builder.load_string()` in the module that defines the widget
- Global styles go in `ui/theme.kv`
- Use `dp()` for sizes and `sp()` for font sizes
- Always reference `root.*` properties, not hardcoded values

---

## 5. Git Workflow

### Branch Naming

| Prefix | Use Case | Example |
|--------|----------|---------|
| `feature/` | New features | `feature/group-chat-ui` |
| `fix/` | Bug fixes | `fix/message-decryption-error` |
| `security/` | Security patches | `security/update-crypto-lib` |
| `docs/` | Documentation | `docs/api-reference-update` |
| `refactor/` | Code improvements | `refactor/firebase-client` |

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `build`, `ci`, `security`

**Examples:**

```
feat(crypto): add AES key rotation for group chats
fix(desktop): resolve message scroll position on new message
security(crypto): update PBKDF2 iterations to 600,000
docs(api): add firebase_client method documentation
```

---

## 6. Pull Request Process

1. **Fork** the repository and create a feature branch
2. **Implement** your changes following the code style guidelines
3. **Test** your changes manually (run both desktop and mobile entry points)
4. **Lint** your code: `black . && isort . && flake8 . && mypy core/`
5. **Submit** a Pull Request with:
   - Clear title following commit convention
   - Description of changes and motivation
   - Screenshots/recordings for UI changes
   - Security implications noted (if any)

### PR Review Checklist

Reviewers will verify:

- [ ] Code follows PEP 8 and project conventions
- [ ] All public functions have type hints and docstrings
- [ ] No plaintext data is sent to Firebase
- [ ] No crypto operations on the main thread
- [ ] Desktop imports don't reference mobile modules (and vice versa)
- [ ] Existing tests pass
- [ ] No new security vulnerabilities introduced

---

## 7. Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=core --cov-report=html

# Run specific test file
pytest tests/test_crypto_engine.py -v
```

### Test Structure

```
tests/
├── test_crypto_engine.py     # Unit tests for encryption/decryption
├── test_firebase_client.py   # Mock-based API tests
├── test_file_manager.py      # File I/O tests
└── conftest.py               # Shared fixtures
```

### Writing Tests

```python
import pytest
from core.crypto_engine import (
    generate_rsa_keypair,
    encrypt_message,
    decrypt_message,
)

class TestMessageEncryption:
    """Tests for the message encryption pipeline."""

    def test_encrypt_decrypt_roundtrip(self) -> None:
        """A message encrypted for a recipient can be decrypted."""
        priv, pub = generate_rsa_keypair()
        plaintext = "Hello, Aegis!"

        payload = encrypt_message(plaintext, [pub])
        decrypted = decrypt_message(payload, "0", priv)

        assert decrypted == plaintext

    def test_wrong_key_fails(self) -> None:
        """Decryption with wrong private key raises InvalidTag."""
        _, pub1 = generate_rsa_keypair()
        priv2, _ = generate_rsa_keypair()

        payload = encrypt_message("secret", [pub1])

        with pytest.raises(Exception):
            decrypt_message(payload, "0", priv2)
```

---

## 8. Security Vulnerability Reporting

**DO NOT** open a public GitHub issue for security vulnerabilities.

### Responsible Disclosure

1. Email security findings to: `security@aegis-messenger.example`
2. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested fix (if any)
3. We will respond within **48 hours** with:
   - Acknowledgment of receipt
   - Initial assessment
   - Timeline for fix

### Scope

| In Scope | Out of Scope |
|----------|-------------|
| Cryptographic weaknesses | Social engineering |
| Key management flaws | Physical device attacks |
| Firebase rule bypasses | DoS attacks |
| Authentication bypasses | Third-party library 0-days |
| Data leakage | Issues in Firebase itself |

---

## 9. Architecture Rules

### Non-Negotiable Rules

These rules must **never** be violated:

1. **Zero Plaintext in Transit:** No unencrypted message content or AES keys may be sent to Firebase
2. **Build-Time Separation:** Desktop and Mobile UI modules must remain physically separated with no cross-imports
3. **Non-Blocking UI:** All crypto and network calls must be in background threads
4. **No SDK Dependencies:** Firebase interactions must use REST APIs only (via `requests`)
5. **Type Safety:** All public API functions must have complete type annotations

### Import Boundary Rules

```
✅ ALLOWED:
  core/* → standard library, cryptography, requests
  ui/shared/* → kivy, kivymd
  ui/desktop/* → core/*, ui/shared/*
  ui/mobile/* → core/*, ui/shared/*
  main_desktop.py → ui/desktop/*, ui/shared/*, core/*
  main_mobile.py → ui/mobile/*, ui/shared/*, core/*

❌ FORBIDDEN:
  core/* → kivy, kivymd, ui/*
  ui/desktop/* → ui/mobile/*
  ui/mobile/* → ui/desktop/*
  main_desktop.py → ui/mobile/*
  main_mobile.py → ui/desktop/*
```

Violating these rules will result in a bloated binary with unused code and potential runtime errors on the wrong platform.
