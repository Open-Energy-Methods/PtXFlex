"""Hermetic F3-D provider parsing, physical conversion and gate regressions.

No synthetic fixture is ever labelled as an observed year.
"""
from datetime import datetime,timedelta,timezone
import hashlib
import struct
import xml.etree.ElementTree as ET
import numpy as np
import pytest

from ptxflex import f3d_live_entsoe as market
from ptxflex import f3d_live_era5 as weather
from ptxflex import f3d_live_provider_pair_gate as pair


def fake_a44(*,curve="A03",domain="10YNL----------L",
             start="2023-01-01T00:00Z",end="2023-01-01T03:00Z",
             points=((1,-10.0),(3,42.5)),resolution="PT60M"):
    root=ET.Element("Publication_MarketDocument")
    ET.SubElement(root,"type").text="A44"
    ts=ET.SubElement(root,"TimeSeries")
    for name,content in (
       ("in_Domain.mRID",domain),("out_Domain.mRID",domain),
       ("currency_Unit.name","EUR"),("price_Measure_Unit.name","MWH"),
       ("curveType",curve)
    ):
        ET.SubElement(ts,name).text=content
    p=ET.SubElement(ts,"Period")
    ET.SubElement(p,"resolution").text=resolution
    iv=ET.SubElement(p,"timeInterval")
    ET.SubElement(iv,"start").text=start
    ET.SubElement(iv,"end").text=end
    for pos,price in points:
        point=ET.SubElement(p,"Point")
        ET.SubElement(point,"position").text=str(pos)
        ET.SubElement(point,"price.amount").text=str(price)
    return ET.tostring(root,encoding="utf-8")


def test_a03_source_semantics_and_negative_price_preservation():
    raw=fake_a44()
    slots=market.xml_native_price_slots(raw)
    epoch=datetime(2023,1,1,tzinfo=timezone.utc)
    hourly=[slots[epoch+timedelta(hours=i)] for i in range(3)]
    assert hourly==[-10.0,-10.0,42.5]
    assert len(slots)==12


def test_native_a01_rejects_omitted_positions_and_wrong_bidding_zone():
    with pytest.raises(ValueError,match="A01"):
        market.xml_native_price_slots(fake_a44(curve="A01"))
    with pytest.raises(ValueError,match="wrong zone"):
        market.xml_native_price_slots(fake_a44(domain="10YDE-----XXX"))


def test_original_price_2023_archive_hash_is_registered_and_f64_deterministic():
    assert market.FROZEN_2023_PRICE_F64_SHA=="e67f59598079303df0c51a553904d2352a939ed7439af73ccbfb3daab9d667b6"
    assert market.f64sha([1.0,-25.0])==hashlib.sha256(
        struct.pack("<d",1.0)+struct.pack("<d",-25.0)).hexdigest()


def test_source_price_requests_bracket_utc_2022_2024():
    assert market.months_bracketing_year(2022)[0]==(2021,12)
    assert market.months_bracketing_year(2024)[-1]==(2025,1)
    assert len(market.months_bracketing_year(2024))==14


def test_era5_leap_month_native_100m_source_request():
    r=weather.request_for(2024,2)
    assert len(r["day"])==29
    assert r["day"][-1]=="29"
    assert r["year"]==["2024"]
    assert r["area"]==[52.75,3.25,52.25,3.75]
    assert "100m_u_component_of_wind" in r["variable"]
    assert "10m_v_component_of_wind" in r["variable"]
    assert r["download_format"]=="unarchived"


def test_wind_original_farm_curve_rated_cutout_and_maximum():
    hub_to_100=(120.0/100.0)**0.11
    u=np.array([0.0,2.0,3.0,9.0,13.0,22.0,25.0,26.0])/hub_to_100
    v=np.zeros_like(u)
    result=weather.original_farm_mw_from_u100_v100(u,v)
    assert result.shape==(8,)
    assert result[0]==0
    assert result[1]==0
    assert result[2]>=0
    assert 0<result[3]<weather.FARM_LIMIT_MW
    assert result[4]==pytest.approx(weather.FARM_LIMIT_MW)
    assert result[5]==pytest.approx(weather.FARM_LIMIT_MW)
    assert result[6]==pytest.approx(0.0,abs=1e-10)
    assert result[7]==0.0


@pytest.mark.parametrize("bad",[float("nan"),float("inf")])
def test_wind_nonfinite_cannot_be_accepted(bad):
    with pytest.raises(ValueError,match="invalid original"):
        weather.original_farm_mw_from_u100_v100([bad],[0])


def test_2023_reference_gate_rejects_missing_calendar_source(tmp_path):
    file=tmp_path/"source.csv"
    file.write_text("timestamp_utc,wind_available_mw\n2023-01-01T00:00:00Z,0\n")
    with pytest.raises(ValueError,match="missing hours"):
        pair.validate_2023_csv(file,"wind_available_mw",cap=weather.FARM_LIMIT_MW)
