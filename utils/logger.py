import sys
from pathlib import Path
from loguru import logger

# 프로젝트 루트 경로 설정
# 이 파일의 위치(utils/logger.py)를 기준으로 두 단계 상위 디렉토리
ROOT_DIR = Path(__file__).parent.parent

# 로그 파일이 저장될 경로
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)  # 로그 폴더가 없으면 생성

# 로그 파일 경로 설정 (일별로 파일 생성)
log_file_path = LOG_DIR / "backend_app_{time:YYYY-MM-DD}.log"

# 기본 로깅 설정 제거
logger.remove()

# 콘솔(stdout) 로거 추가
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# 파일 로거 추가
logger.add(
    log_file_path,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    rotation="00:00",  # 매일 자정에 새 파일 생성
    retention="7 days",  # 7일간 로그 보관
    enqueue=True,  # 비동기 로깅 활성화
    serialize=False, # JSON 형식이 아닌 텍스트로 저장
    encoding="utf-8"
)

logger.info("Logger initialized. Logs will be saved to '{}'", LOG_DIR.absolute())

# 다른 모듈에서 `from utils.logger import logger`로 가져가서 사용할 수 있도록 함
__all__ = ["logger"]
