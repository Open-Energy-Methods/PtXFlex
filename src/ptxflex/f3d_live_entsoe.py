"""Acquire native Dutch ENTSO-E A44 XML, reconstruct exact UTC prices.

Only run with a private repository Actions secret or a private local key.
No raw provider document, normalized price sequence or secret belongs in Git.
This file intentionally reimplements the original PyNEXUS A03 expansion
rather than relying on entsoe-py's pandas hourly conversion.
"""
from __future__ import annotations

import argparse
import calendar
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import struct
from xml.etree import ElementTree as ET

YEARS = {2022:8760, 2023:8760, 2024:8784}
ZONE = "10YNL----------L"
FROZEN_2023_PRICE_F64_SHA = "e67f59598079303df0c51a553904d2352a939ed7439af73ccbfb3daab9d667b6"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def local(node):
    return node.tag.rsplit("}", 1)[-1]


def child(node, tag):
    found = [item for item in node if local(item) == tag]
    require(len(found)==1, "expected one official A44 element "+tag)
    return found[0]


def value(node, tag):
    data = child(node, tag).text
    require(isinstance(data,str) and bool(data.strip()), "missing A44 "+tag)
    return data.strip()


def utc_instant(data):
    stamp = datetime.fromisoformat(data.replace("Z","+00:00"))
    require(stamp.tzinfo is not None, "A44 timestamp must be timezone-aware")
    return stamp.astimezone(timezone.utc)


def xml_native_price_slots(raw):
    """Return source-defined quarter-hour slots, retaining A03 block semantics."""
    require(isinstance(raw,bytes) and 0<len(raw)<=20_000_000 and
            b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper(),
            "unsafe or empty A44 provider document")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        raise ValueError("unparseable official A44 XML") from None
    require(local(root)=="Publication_MarketDocument" and value(root,"type")=="A44",
            "provider response is not original A44 XML")
    slots = {}
    series=[node for node in root if local(node)=="TimeSeries"]
    require(bool(series), "official A44 contains no price timeseries")
    for ts in series:
        require(value(ts,"in_Domain.mRID")==ZONE and value(ts,"out_Domain.mRID")==ZONE
                and value(ts,"currency_Unit.name")=="EUR"
                and value(ts,"price_Measure_Unit.name")=="MWH",
                "wrong zone, currency or market price unit")
        curve = value(ts,"curveType")
        require(curve in ("A03","A01"),"unqualified A44 curve type")
        periods=[x for x in ts if local(x)=="Period"]
        require(bool(periods),"A44 TimeSeries missing period")
        for period in periods:
            resolution=value(period,"resolution")
            require(resolution in ("PT60M","PT15M"),"unexpected market interval resolution")
            minutes=60 if resolution=="PT60M" else 15
            interval=child(period,"timeInterval")
            start=utc_instant(value(interval,"start"))
            end=utc_instant(value(interval,"end"))
            seconds=(end-start).total_seconds()
            require(seconds>0 and seconds%(minutes*60)==0 and seconds<=31*86400,
                    "invalid A44 interval endpoints")
            count=int(seconds//(minutes*60))
            points=[]
            for p in period:
                if local(p)=="Point":
                    position=int(value(p,"position"))
                    amount=float(value(p,"price.amount"))
                    require(__import__("math").isfinite(amount),"nonfinite official market price")
                    points.append((position,amount))
            require(points and points[0][0]==1,"A44 missing beginning of block")
            require(all(1<=pos<=count for pos,_ in points) and
                    all(a[0]<b[0] for a,b in zip(points,points[1:])),
                    "A44 block positions invalid or repeated")
            if curve=="A01":
                require(len(points)==count and all(k==i+1 for i,(k,_) in enumerate(points)),
                        "A01 sequential curve has missing positions")
            for i,(position,amount) in enumerate(points):
                following=points[i+1][0] if i+1<len(points) else count+1
                for position_zero in range(position-1,following-1):
                    stamp=start+timedelta(minutes=minutes*position_zero)
                    for q in range(minutes//15):
                        instant=stamp+timedelta(minutes=15*q)
                        require(instant not in slots,"overlapping raw A44 price intervals")
                        slots[instant]=amount
    return slots


def reconstruct_utc_year(source_documents, year):
    """All 15-minute slots required; duration-weighted hourly values.

    A03 repeating the last provider value is source-defined, not imputation.
    """
    require(year in YEARS,"only registered 2022, 2023 and 2024 years")
    slots={}
    for original in source_documents:
        doc=xml_native_price_slots(original)
        for stamp,price in doc.items():
            require(stamp not in slots,"cross-document market interval overlap")
            slots[stamp]=price
    epoch=datetime(year,1,1,tzinfo=timezone.utc)
    out=[]
    for h in range(YEARS[year]):
        start=epoch+timedelta(hours=h)
        values=[slots.get(start+timedelta(minutes=15*j)) for j in range(4)]
        require(all(x is not None for x in values),"unreported official UTC price quarter hour")
        out.append(sum(values)/4.0 if values.count(values[0])!=4 else values[0])
    # Source requests bracket extra hours: they may be present, but all actual
    # target-year intervals are accounted for and no duplicates are accepted.
    return out


def f64sha(values):
    return hashlib.sha256(b"".join(struct.pack("<d",v) for v in values)).hexdigest()


def months_bracketing_year(year):
    return [(year-1,12)]+[(year,m) for m in range(1,13)]+[(year+1,1)]


def acquire(year, output_root):
    require(year in YEARS,"unregistered historical year")
    output_root=Path(output_root).resolve()
    require(not output_root.exists(),"cannot replace original provider data")
    key=os.environ.get("ENTSOE_API_KEY","").strip()
    require(key and len(key)>10,"ENTSOE_API_KEY is unavailable in this runner")
    from entsoe import EntsoeRawClient
    import pandas as pd
    client=EntsoeRawClient(api_key=key)
    rawdir=output_root/"original_xml"
    rawdir.mkdir(parents=True,exist_ok=False)
    manifest={
        "schema_version":"ptxflex.f3d_entsoe_native_monthly_price_source.v1",
        "provider":"ENTSO-E Transparency Platform original A44 XML",
        "year":year,"zone":"NL","timezone":"Europe/Amsterdam",
        "source_data_may_be_provider_licensed":True,
        "price_unit":"EUR/MWh",
        "status":"INCOMPLETE_PROVIDER_ORIGINAL_COLLECTION",
        "raw_monthly_documents":[],
        "original_2023_float64_reference_match":None,
        "not_an_industrial_plant_price_forecast":True,
        "independent_peer_review_complete":False
    }
    try:
        for yy,mm in months_bracketing_year(year):
            start=pd.Timestamp(year=yy,month=mm,day=1,tz="Europe/Amsterdam")
            end=start+pd.DateOffset(months=1)
            try:
                reply=client.query_day_ahead_prices("NL",start=start,end=end)
            except Exception as exc:
                raise RuntimeError("ENTSO-E provider fetch failed for "+
                                   str(yy)+"-"+str(mm).zfill(2)+
                                   " ("+type(exc).__name__+"); secret and server response suppressed") from None
            raw=reply.encode("utf-8") if isinstance(reply,str) else reply
            require(isinstance(raw,bytes),"A44 provider returned unsupported document")
            require(key.encode() not in raw,"provider document reflected credential")
            # Reject unsupported XML before any archival success claim.
            parsed=xml_native_price_slots(raw)
            require(bool(parsed),"empty A44 time series")
            filename="NL_A44_"+str(yy)+str(mm).zfill(2)+".xml"
            (rawdir/filename).write_bytes(raw)
            manifest["raw_monthly_documents"].append({
                "filename":filename,"sha256":hashlib.sha256(raw).hexdigest(),
                "bytes":len(raw),"quarter_hours_after_source_A03_expansion":len(parsed)
            })
            print("Validated original A44 XML",year,yy,mm,"bytes",len(raw),flush=True)
        values=reconstruct_utc_year(
            [(rawdir/r["filename"]).read_bytes() for r in manifest["raw_monthly_documents"]],year)
        sha=f64sha(values)
        ismatch=(sha==FROZEN_2023_PRICE_F64_SHA) if year==2023 else None
        manifest.update({
            "status":"UTC_SOURCE_RECONSTRUCTED_NOT_EXTERNALLY_REVIEWED",
            "hours":len(values),
            "float64_little_endian_SHA256":sha,
            "original_2023_float64_reference_match":ismatch,
            "chronology_exact_UTC_no_gap_no_duplicate":True,
            "observed_data_processed_not_a_market_forecast":True,
        })
        if year==2023:
            require(ismatch,"2023 source-refetched price differs from frozen original SHA; inspect provider revisions and A03 logic")
        with (output_root/"normalized_UTC_price.csv").open("w",encoding="utf-8",newline="") as f:
            import csv
            writer=csv.writer(f)
            writer.writerow(["timestamp_utc","day_ahead_eur_mwh"])
            epoch=datetime(year,1,1,tzinfo=timezone.utc)
            for h,v in enumerate(values):
                writer.writerow([(epoch+timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ"),format(v,".17g")])
        manifest["normalized_csv_SHA256"]=hashlib.sha256(
            (output_root/"normalized_UTC_price.csv").read_bytes()).hexdigest()
        return manifest
    finally:
        (output_root/"provenance.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--year",type=int,required=True,choices=sorted(YEARS))
    ap.add_argument("--output",required=True)
    args=ap.parse_args(argv)
    m=acquire(args.year,args.output)
    print(json.dumps({k:v for k,v in m.items() if k not in ("raw_monthly_documents",)},
                     indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
