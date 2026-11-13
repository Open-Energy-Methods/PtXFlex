import argparse
import json
from pathlib import Path
from .model import solve


def main(argv=None):
    p = argparse.ArgumentParser(description="Run hypothetical methanol MILP")
    p.add_argument("source", type=Path)
    p.add_argument("--emissions-cap-kgco2e", type=float)
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    obj = json.loads(args.source.read_text(encoding="utf-8"))
    result = solve(obj, emissions_cap_kgco2e=args.emissions_cap_kgco2e)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

if __name__ == "__main__":
    main()
