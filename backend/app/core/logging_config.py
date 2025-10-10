import sys
import logging
from pathlib import Path
from loguru import logger
from app.core.config import get_settings

class InterceptHandler(logging.Handler):
    """
    표준 로깅(stdlib logging)의 로그를 loguru가 가로채서 처리하도록 하는 핸들러.
    Uvicorn, FastAPI 등의 내부 로그도 loguru 포맷으로 일관되게 출력 가능.
    """
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def setup_logging():
    """
    loguru를 사용하여 로깅 시스템을 설정합니다.
    환경 변수(LOG_LEVEL, LOG_FORMAT)에 따라 동적으로 설정을 변경합니다.
    """
    settings = get_settings()
    # 기존의 모든 로거를 제거하고 새로 설정 시작
    logger.remove()

    # 로그 파일이 저장될 디렉토리 설정 (프로젝트 루트/logs)
    LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"
    LOG_DIR.mkdir(exist_ok=True)
    log_file_path = LOG_DIR / "backend_app_{time:YYYY-MM-DD}.log"

    # 1. 콘솔 로거 추가 (가독성 좋은 포맷)
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL.upper(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # 2. 파일 로거 추가 (환경변수에 따라 text/json 포맷 결정)
    logger.add(
        log_file_path,
        level=settings.LOG_LEVEL.upper(),
        # JSON 포맷이 아닐 때만 사용할 일반 텍스트 포맷
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="00:00",  # 매일 자정에 새 파일 생성
        retention="30 days", # 30일간 로그 보관
        enqueue=settings.LOG_ENQUEUE,
        serialize=(settings.LOG_FORMAT.lower() == "json"), # LOG_FORMAT 값에 따라 직렬화 결정
        encoding="utf-8",
        backtrace=True,    # 예외 발생 시 스택 트레이스 전체 기록
        diagnose=True,     # 변수 값 등 진단 정보 추가
    )

    # 3. 표준 로깅(stdlib) 핸들러를 InterceptHandler로 교체
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    logger.info(f"Logger initialized with level '{settings.LOG_LEVEL}' and format '{settings.LOG_FORMAT}'.")
    logger.info(f"Logs will be saved to '{LOG_DIR.absolute()}'")
