"""
포트폴리오 스냅샷 관리
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
from loguru import logger

from app.models.schemas import Trade


class SnapshotManager:
    """포트폴리오 스냅샷 & 거래 로그 관리"""

    def __init__(self, base_dir: str = "data/snapshots"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _snapshot_path(self, date: datetime) -> Path:
        return self.base_dir / f"snapshot_{date:%Y%m%d}.json"

    def save_snapshot(self, date: datetime, snapshot: Dict):
        """
        스냅샷 저장
        snapshot = {
            "date": "2025-10-10",
            "cash": 12000000,
            "positions": {"005930": {"quantity": 100, "avg_price": 72000}},
            "total_asset": 13500000
        }
        """
        path = self._snapshot_path(date)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 스냅샷 저장: {path.name}")

    def load_latest_snapshot(self, date: datetime) -> Optional[Dict]:
        """특정 날짜 이전의 최신 스냅샷 로드"""
        candidates: List[Path] = sorted(self.base_dir.glob("snapshot_*.json"))
        target = None
        for candidate in candidates:
            snap_date_str = candidate.stem.split("_")[1]
            try:
                snap_date = datetime.strptime(snap_date_str, "%Y%m%d")
                if snap_date <= date and (target is None or snap_date > datetime.strptime(target.stem.split("_")[1], "%Y%m%d")):
                    target = candidate
            except ValueError:
                logger.warning(f"잘못된 형식의 스냅샷 파일명: {candidate.name}")
                continue

        if not target:
            return None

        with open(target, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"✅ 스냅샷 로드: {target.name}")
        return data

    def replay_from_snapshot(
        self,
        snapshot: Dict,
        trades: List[Trade],
        end_date: datetime
    ) -> Dict:
        """
        스냅샷 이후 거래만 재생해 최종 포지션/현금을 계산
        """
        positions = {code: details["quantity"] for code, details in snapshot.get("positions", {}).items()}
        cash = snapshot.get("cash", 0)

        for trade in trades:
            try:
                # 정확한 시간 비교 (기본)
                snapshot_timestamp_str = snapshot['timestamp']
                trade_time_str = trade.trade_time or '000000'
                
                snapshot_dt = datetime.fromisoformat(snapshot_timestamp_str)
                trade_dt = datetime.strptime(f"{trade.trade_date}{trade_time_str}", "%Y%m%d%H%M%S")

                if trade_dt <= snapshot_dt:
                    continue

            except (KeyError, ValueError):
                # 타임스탬프 부재 또는 형식 오류 시, 날짜 기준으로만 필터링 (폴백)
                logger.warning(f"스냅샷 타임스탬프 비교 오류. 날짜 기준으로 폴백합니다. snapshot={snapshot.get('date')}, trade={trade.trade_date}")
                try:
                    snapshot_date_dt = datetime.strptime(snapshot['date'], "%Y-%m-%d")
                    trade_date_dt = datetime.strptime(trade.trade_date, "%Y%m%d")
                    if trade_date_dt <= snapshot_date_dt:
                        continue
                except (ValueError, KeyError):
                    continue # 날짜 파싱도 실패하면 해당 거래는 건너뜀

            if trade.trade_type == "buy":
                cash -= trade.amount + trade.fee
                positions[trade.stock_code] = positions.get(trade.stock_code, 0) + trade.quantity
            else:
                cash += trade.amount - trade.fee - trade.tax
                positions[trade.stock_code] = positions.get(trade.stock_code, 0) - trade.quantity
                if positions.get(trade.stock_code, 0) <= 0:
                    positions.pop(trade.stock_code, None)

        return {
            "date": end_date.strftime("%Y-%m-%d"),
            "cash": cash,
            "positions": positions
        }
