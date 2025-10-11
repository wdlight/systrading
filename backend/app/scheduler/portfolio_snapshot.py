"""
포트폴리오 스냅샷 자동 저장
"""

import json
from pathlib import Path
from datetime import datetime
from loguru import logger

from app.core.config import Settings
from app.core.korea_invest import KoreaInvestAPIService
from app.services.snapshot_manager import SnapshotManager


async def save_portfolio_snapshot():
    """주기적으로 포트폴리오 스냅샷을 저장하는 스케줄링 작업"""

    logger.info("📸 포트폴리오 스냅샷 저장을 시작합니다.")

    try:
        # 서비스 직접 초기화
        settings = Settings()
        korea_invest = KoreaInvestAPIService(settings)

        if not korea_invest or not korea_invest.is_connected:
            logger.error("한투 API에 연결되지 않아 스냅샷을 저장할 수 없습니다.")
            return

        # 계좌 잔고 조회
        balance = await korea_invest.get_account_balance()
        if not balance:
            logger.error("계좌 잔고를 조회할 수 없어 스냅샷을 저장할 수 없습니다.")
            return

        # 스냅샷 데이터 구성
        now = datetime.now()
        snapshot_data = {
            "date": now.strftime("%Y-%m-%d"),
            "timestamp": now.isoformat(),
            "cash": balance.get("available_cash", 0),
            "positions": {p["stock_code"]: {"quantity": p["quantity"], "avg_price": p["avg_price"]} for p in balance.get("positions", [])},
            "total_asset": balance.get("total_value", 0)
        }

        # 스냅샷 저장
        snapshot_manager = SnapshotManager()
        snapshot_manager.save_snapshot(now, snapshot_data)

    except Exception as e:
        logger.error(f"❌ 포트폴리오 스냅샷 저장 중 오류 발생: {e}", exc_info=True)
