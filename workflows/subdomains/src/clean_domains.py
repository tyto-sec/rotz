import re
import sys
from pathlib import Path


def clean_domain(domain: str) -> str:
    domain = domain.strip()
    domain = re.sub(r'^https?://', '', domain)
    domain = domain.split('/')[0]
    domain = domain.split(':')[0]
    if domain.endswith('.'):
        domain = domain[:-1]
    domain = domain.split('?')[0]
    domain = domain.split('#')[0]

    return domain.strip().lower()


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: clean_domains.py <file>", file=sys.stderr)
        return 1

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 1

    cleaned = []
    with path.open('r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            value = clean_domain(line)
            if value:
                cleaned.append(value)

    cleaned = sorted(set(cleaned))
    tmp_path = path.with_suffix(path.suffix + '.tmp')
    with tmp_path.open('w', encoding='utf-8') as f:
        f.write("\n".join(cleaned))
        if cleaned:
            f.write("\n")

    tmp_path.replace(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
