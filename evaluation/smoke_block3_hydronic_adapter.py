from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests


TESTCASE = "bestest_hydronic_heat_pump"
DEFAULT_BOPTEST_URL = "http://localhost:8000"
DEFAULT_OUTPUT_DIR = Path("reports")
STEP_SEC = 900
SELECT_TIMEOUT = 300
ADVANCE_TIMEOUT = 60
HTTP_RETRIES = 3


CONDITIONS: dict[str, dict[str, float]] = {
    "baseline_no_override": {},
    "low_heat_override": {
        "oveTSet_activate": 1,
        "oveTSet_u": 288.15,
        "oveHeaPumY_activate": 1,
        "oveHeaPumY_u": 0.0,
        "ovePum_activate": 1,
        "ovePum_u": 0.0,
        "oveFan_activate": 1,
        "oveFan_u": 0.0,
    },
    "high_heat_override": {
        "oveTSet_activate": 1,
        "oveTSet_u": 297.15,
        "oveHeaPumY_activate": 1,
        "oveHeaPumY_u": 1.0,
        "ovePum_activate": 1,
        "ovePum_u": 1.0,
        "oveFan_activate": 1,
        "oveFan_u": 1.0,
    },
}


def k_to_c(value: float) -> float:
    return float(value) - 273.15 if float(value) > 200.0 else float(value)


def get_float(payload: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = payload.get(key, default)
    if isinstance(value, dict):
        value = value.get("value", default)
    return float(value)


def request_json(
    session: requests.Session,
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 60,
    retries: int = HTTP_RETRIES,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            if method == "GET":
                response = session.get(url, timeout=timeout)
            elif method == "POST":
                response = session.post(url, json=payload or {}, timeout=timeout)
            elif method == "PUT":
                response = session.put(url, json=payload or {}, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            if response.status_code in (500, 502, 503, 504):
                time.sleep(2**attempt)
                continue
            response.raise_for_status()
            return response.json()
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_error = exc
            print(f"  Retry {attempt + 1}/{retries}: {exc}")
            time.sleep(2**attempt)
    raise RuntimeError(f"Request failed: {method} {url}") from last_error


def select_testcase(session: requests.Session, base_url: str) -> str:
    data = request_json(
        session,
        "POST",
        f"{base_url}/testcases/{TESTCASE}/select",
        timeout=SELECT_TIMEOUT,
    )
    testid = data.get("testid")
    if not testid:
        raise RuntimeError(f"No testid in select response: {data}")
    return str(testid)


def initialize(session: requests.Session, base_url: str, testid: str, start_time: float) -> dict[str, Any]:
    request_json(session, "PUT", f"{base_url}/step/{testid}", {"step": STEP_SEC}, timeout=30)
    data = request_json(
        session,
        "PUT",
        f"{base_url}/initialize/{testid}",
        {"start_time": float(start_time), "warmup_period": 0},
        timeout=SELECT_TIMEOUT,
    )
    return data.get("payload", data)


def advance(session: requests.Session, base_url: str, testid: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = request_json(
        session,
        "POST",
        f"{base_url}/advance/{testid}",
        payload,
        timeout=ADVANCE_TIMEOUT,
    )
    return data.get("payload", data)


def stop(session: requests.Session, base_url: str, testid: str) -> None:
    try:
        request_json(session, "PUT", f"{base_url}/stop/{testid}", timeout=10, retries=1)
    except Exception:
        pass


def row_from_payload(condition: str, step_index: int, payload: dict[str, Any], action: dict[str, Any]) -> dict[str, Any]:
    return {
        "condition": condition,
        "step_index": step_index,
        "time_s": get_float(payload, "time", float(step_index * STEP_SEC)),
        "reaTZon_c": k_to_c(get_float(payload, "reaTZon_y")),
        "reaTSup_c": k_to_c(get_float(payload, "reaTSup_y")),
        "reaTSetHea_c": k_to_c(get_float(payload, "reaTSetHea_y")),
        "reaTSetCoo_c": k_to_c(get_float(payload, "reaTSetCoo_y")),
        "reaPHeaPum_w": get_float(payload, "reaPHeaPum_y"),
        "reaPFan_w": get_float(payload, "reaPFan_y"),
        "reaPPumEmi_w": get_float(payload, "reaPPumEmi_y"),
        "reaCOP": get_float(payload, "reaCOP_y"),
        "action_json": json.dumps(action, sort_keys=True),
    }


def run_condition(
    session: requests.Session,
    base_url: str,
    condition: str,
    action: dict[str, Any],
    start_time: float,
    steps: int,
) -> list[dict[str, Any]]:
    testid = select_testcase(session, base_url)
    print(f"[{condition}] testid={testid}")
    try:
        payload = initialize(session, base_url, testid, start_time)
        rows = [row_from_payload(condition, 0, payload, action)]
        for step in range(1, steps + 1):
            payload = advance(session, base_url, testid, action)
            rows.append(row_from_payload(condition, step, payload, action))
        return rows
    finally:
        stop(session, base_url, testid)


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for condition, sub in df.groupby("condition", sort=False):
        post = sub[sub["step_index"] > 0]
        rows.append(
            {
                "condition": condition,
                "n_steps": int(post.shape[0]),
                "t_zone_initial_c": float(sub.iloc[0]["reaTZon_c"]),
                "t_zone_final_c": float(sub.iloc[-1]["reaTZon_c"]),
                "t_zone_delta_c": float(sub.iloc[-1]["reaTZon_c"] - sub.iloc[0]["reaTZon_c"]),
                "mean_heat_pump_power_w": float(post["reaPHeaPum_w"].mean()),
                "mean_fan_power_w": float(post["reaPFan_w"].mean()),
                "mean_pump_power_w": float(post["reaPPumEmi_w"].mean()),
                "mean_t_supply_c": float(post["reaTSup_c"].mean()),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--boptest-url", default=DEFAULT_BOPTEST_URL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--start-time", type=float, default=0.0)
    parser.add_argument("--steps", type=int, default=8)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})

    version = request_json(session, "GET", f"{args.boptest_url}/version", timeout=20)
    print("BOPTEST version:", version)

    rows: list[dict[str, Any]] = []
    for condition, action in CONDITIONS.items():
        rows.extend(run_condition(session, args.boptest_url, condition, action, args.start_time, args.steps))

    df = pd.DataFrame(rows)
    summary = build_summary(df)

    csv_path = args.output_dir / "block3_hydronic_heat_pump_adapter_smoke.csv"
    summary_path = args.output_dir / "block3_hydronic_heat_pump_adapter_smoke_summary.csv"
    json_path = args.output_dir / "block3_hydronic_heat_pump_adapter_smoke_summary.json"

    df.to_csv(csv_path, index=False)
    summary.to_csv(summary_path, index=False)
    json_path.write_text(summary.to_json(orient="records", indent=2), encoding="utf-8")

    print("\nSummary:")
    print(summary.to_string(index=False))
    print(f"\nSaved trace: {csv_path}")
    print(f"Saved summary: {summary_path}")
    print(f"Saved summary JSON: {json_path}")

    low = summary.set_index("condition").loc["low_heat_override"]
    high = summary.set_index("condition").loc["high_heat_override"]
    checks = {
        "high_power_gt_low_power": bool(high["mean_heat_pump_power_w"] > low["mean_heat_pump_power_w"]),
        "high_final_temp_ge_low_final_temp": bool(high["t_zone_final_c"] >= low["t_zone_final_c"]),
    }
    print("\nAcceptance checks:")
    for key, value in checks.items():
        print(f"  {key}: {value}")
    if not all(checks.values()):
        raise SystemExit("Smoke test FAILED adapter acceptance checks.")


if __name__ == "__main__":
    main()
