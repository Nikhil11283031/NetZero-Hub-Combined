"""Create missing local settings without changing existing database passwords."""
from pathlib import Path
import re
import secrets

ROOT = Path(__file__).resolve().parents[1]
SECRET_KEYS = {"MYSQL_PASSWORD", "MYSQL_ROOT_PASSWORD", "DJANGO_SECRET_KEY",
               "PROVIDER_API_KEY", "INTEGRATION_API_KEYS", "NZ_INTERNAL_TOKEN"}
DEMO_PASSWORDS = {"DEMO_RESIDENT_PASSWORD": "Resident927!Local",
                  "DEMO_STAFF_PASSWORD": "Provider927!Local"}


def configure(root=ROOT):
    target = root / ".env"
    template = (root / "env.example").read_text(encoding="utf-8-sig")
    existing = target.read_text(encoding="utf-8-sig") if target.exists() else template
    keys = {}
    for line in existing.splitlines():
        key, separator, value = line.partition("=")
        if separator and re.fullmatch(r"[A-Z_]+", key):
            keys[key] = value
    for line in template.splitlines():
        key, separator, value = line.partition("=")
        if separator and re.fullmatch(r"[A-Z_]+", key) and key not in keys:
            existing = existing.rstrip() + "\n" + line + "\n"
            keys[key] = value
    replacements = {}
    for key in SECRET_KEYS:
        if not keys.get(key, "").strip() or keys[key].startswith("CHANGE-ME"):
            replacements[key] = secrets.token_hex(32)
    for key, password in DEMO_PASSWORDS.items():
        if not keys.get(key, "").strip():
            replacements[key] = password
    lines = []
    for line in existing.splitlines():
        key = line.partition("=")[0]
        lines.append(f"{key}={replacements[key]}" if key in replacements else line)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Local configuration ready. Existing passwords were preserved.")


if __name__ == "__main__":
    configure()
