"""Use real-source import separately from hypothetical test-case optimization."""
import argparse
import json
from pathlib import Path

from .model import solve


def main(argv=None):
    p=argparse.ArgumentParser(description="PtXFlex source-verified PtX optimization")
    p.add_argument("source",type=Path)
    p.add_argument("--import-pynexus-2023-e",action="store_true",
                   help="ONLY export real 2023 wind and price arrays; cannot run methanol MILP without sourced physical/GWP assumptions")
    p.add_argument("--emissions-cap-kgco2e",type=float)
    p.add_argument("--output",type=Path)
    args=p.parse_args(argv)
    if args.import_pynexus_2023_e:
        if args.emissions_cap_kgco2e is not None:
            p.error("cannot optimize historical import without real GWP source and plant assumptions")
        if args.output is None:
            p.error("original source import requires --output to retain provenance")
        from .observed_sources import write_import
        print(json.dumps(write_import(args.source,args.output),sort_keys=True,indent=2))
        return
    obj=json.loads(args.source.read_text(encoding="utf-8"))
    result=solve(obj,emissions_cap_kgco2e=args.emissions_cap_kgco2e)
    text=json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n"
    if args.output:
        if args.output.exists():
            raise FileExistsError("refusing to overwrite source result")
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding="utf-8")
    else:
        print(text,end="")


if __name__=="__main__":
    main()
