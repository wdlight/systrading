"""
포트폴리오 스냅샷 수동 실행 테스트
"""
import sys
import os
import asyncio

# backend 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.scheduler.portfolio_snapshot import save_portfolio_snapshot
from loguru import logger

async def main():
    """스냅샷 저장 함수를 수동으로 실행"""
    logger.info("=" * 60)
    logger.info("📸 포트폴리오 스냅샷 수동 실행 테스트")
    logger.info("=" * 60)

    try:
        await save_portfolio_snapshot()
        logger.info("✅ 스냅샷 저장 완료")

        # 저장된 파일 확인
        snapshot_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'snapshots')
        if os.path.exists(snapshot_dir):
            files = os.listdir(snapshot_dir)
            logger.info(f"📁 저장된 스냅샷 파일: {len(files)}개")
            for f in files:
                logger.info(f"   - {f}")
        else:
            logger.warning(f"⚠️  스냅샷 디렉토리가 없습니다: {snapshot_dir}")

    except Exception as e:
        logger.error(f"❌ 스냅샷 저장 실패: {e}", exc_info=True)
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
