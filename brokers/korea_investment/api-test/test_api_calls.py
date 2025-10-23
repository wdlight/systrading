"""Manual API smoke tests for Korea Investment endpoints.

Each test uses `KoreaInvestEnv` to obtain fresh tokens and prints the raw
payload to stdout so operators can verify the live response.

Run manually:
    python -m unittest brokers.korea_investment.api-test.test_api_calls
"""

from __future__ import annotations

import json
import logging
import os
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable

try:
    import pandas as pd  # type: ignore
except ImportError:  # pragma: no cover - pandas is optional for these smoke tests
    pd = None

# Ensure project root & backend package are importable
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

try:
    from backend.app.core.config import get_settings
    from brokers.korea_investment.ki_env import KoreaInvestEnv
    from brokers.korea_investment.ki_api import KoreaInvestAPI, APIResponse
except Exception as import_exc:  # pragma: no cover - import guard for clarity
    raise unittest.SkipTest(f"필수 모듈 import 실패: {import_exc}")


class BaseKoreaInvestAPITest(unittest.TestCase):
    """Shared fixture for Korea Investment API integration checks."""

    api: KoreaInvestAPI | None = None
    env: KoreaInvestEnv | None = None
    config: dict[str, Any] | None = None

    @classmethod
    def setUpClass(cls) -> None:
        cls._configure_logging()
        logging.info("=== KoreaInvestEnv 디버그 초기화 시작 ===")
        try:
            settings = get_settings()
            cls.config = {
                **settings.get_korea_invest_config(),
                "custtype": settings.KI_CUSTTYPE,
                "is_paper_trading": settings.KI_IS_PAPER_TRADING,
                "url": settings.KI_API_URL,
                "paper_url": settings.KI_PAPER_URL,
                "websocket_url": settings.KI_WEBSOCKET_URL,
                "paper_websocket_url": settings.KI_PAPER_WEBSOCKET_URL,
                "my_agent": settings.KI_USER_AGENT,
            }
            cls._log_settings_snapshot(settings)
            cls._log_os_environment(prefixes=("KI_", "KIS_", "KOREA_INVEST_"))
            cls._log_config_overview(cls.config or {})
        except Exception as exc:  # pragma: no cover - configuration guard
            raise unittest.SkipTest(f"환경 설정 로드 실패: {exc}")

        try:
            cls.env = KoreaInvestEnv(cls.config)
            base_headers = cls.env.get_base_headers()
            cls._log_env_bootstrap(cls.env, base_headers)
            cls.api = KoreaInvestAPI(cls.config, base_headers=base_headers)
            logging.info("=== KoreaInvestEnv 디버그 초기화 완료 ===")
        except Exception as exc:  # pragma: no cover - token/bootstrap guard
            raise unittest.SkipTest(f"KoreaInvestEnv 초기화 실패: {exc}")

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------
    def _to_serializable(self, obj: Any) -> Any:
        """Convert arbitrary API payload into JSON serialisable data."""
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, (list, tuple, set)):
            return [self._to_serializable(item) for item in obj]
        if isinstance(obj, dict):
            return {key: self._to_serializable(value) for key, value in obj.items()}
        if pd is not None and isinstance(obj, pd.DataFrame):  # type: ignore[arg-type]
            return obj.to_dict(orient="records")
        if isinstance(obj, APIResponse):
            body = obj.get_body()
            return self._to_serializable(vars(body))
        if hasattr(obj, "__dict__"):
            return {key: self._to_serializable(value) for key, value in vars(obj).items()}
        return repr(obj)

    def _print_raw(self, label: str, payload: Any) -> Any:
        serializable = self._to_serializable(payload)
        pretty = json.dumps(serializable, indent=2, ensure_ascii=False)
        print(f"\n[{label}] raw response:\n{pretty}\n")
        return payload

    def _handle_api_response(self, label: str, response: APIResponse | None) -> Any:
        if response is None:
            self._print_raw(label, None)
            self.skipTest("API 응답이 없습니다. 환경/계좌 설정을 확인하세요.")
        body = response.get_body()
        self._print_raw(label, body)
        if not response.is_ok():
            msg = getattr(body, "msg1", "API 오류")
            self.skipTest(f"API 호출 실패: {msg}")
        return body

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------
    @classmethod
    def _configure_logging(cls) -> None:
        """테스트 실행 시 최초 한 번만 루트 로거 포맷을 설정한다."""
        root_logger = logging.getLogger()
        if not root_logger.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        else:
            root_logger.setLevel(logging.INFO)

    @classmethod
    def _log_settings_snapshot(cls, settings: Any) -> None:
        """백엔드 Settings 객체가 어떤 파일과 값을 참조하는지 출력한다."""
        config_class = getattr(settings, "__config__", None) or getattr(settings.__class__, "Config", None)
        env_file = getattr(config_class, "env_file", None)
        if env_file:
            env_path = Path(env_file)
            logging.info("Settings.Config.env_file 경로: %s (exists=%s)", env_path, env_path.exists())
        else:
            logging.warning("Settings.Config.env_file이 정의되어 있지 않습니다.")

        tracked_fields = [
            "KI_API_KEY",
            "KI_SECRET_KEY",
            "KI_ACCOUNT_NUMBER",
            "KI_HTSID",
            "KI_CUSTTYPE",
            "KI_IS_PAPER_TRADING",
            "KI_USER_AGENT",
            "KI_API_URL",
            "KI_PAPER_URL",
            "KI_USING_URL",
        ]
        for field in tracked_fields:
            raw_value = getattr(settings, field, None)
            masked = cls._mask_value(field, raw_value)
            logging.info("Settings.%s = %s", field, masked)

    @classmethod
    def _log_os_environment(cls, prefixes: Iterable[str]) -> None:
        """지정한 prefix로 시작하는 환경 변수 값을 살펴본다."""
        captured: Dict[str, str] = {}
        for key, value in os.environ.items():
            if any(key.startswith(prefix) for prefix in prefixes):
                captured[key] = cls._mask_value(key, value)
        if not captured:
            joined = ", ".join(prefixes)
            logging.warning("현재 프로세스 환경 변수에 %s 접두사를 가진 항목이 없습니다.", joined)
            return
        for key in sorted(captured):
            logging.info("os.environ[%s] = %s", key, captured[key])

    @classmethod
    def _log_config_overview(cls, config: dict[str, Any]) -> None:
        """KoreaInvestEnv에 전달할 config 딕셔너리의 핵심 값을 출력한다."""
        if not config:
            logging.warning("KoreaInvestEnv 초기화에 사용될 config가 비어 있습니다.")
            return
        logging.info("KoreaInvestEnv 초기화에 사용되는 config 키: %s", sorted(config.keys()))
        tracked_keys = [
            "api_key",
            "api_secret_key",
            "paper_api_key",
            "paper_api_secret_key",
            "stock_account_number",
            "custtype",
            "is_paper_trading",
            "url",
            "paper_url",
            "websocket_url",
            "paper_websocket_url",
        ]
        for key in tracked_keys:
            value = config.get(key, "<미정의>")
            masked = cls._mask_value(key, value)
            logging.info("config['%s'] = %s", key, masked)

    @classmethod
    def _log_env_bootstrap(cls, env: KoreaInvestEnv, base_headers: dict[str, Any] | None) -> None:
        """KoreaInvestEnv가 최종적으로 보유한 설정과 헤더를 출력한다."""
        if base_headers is None:
            logging.warning("KoreaInvestEnv에서 base_headers를 가져오지 못했습니다.")
        else:
            for header_key in ("appkey", "appsecret", "authorization"):
                masked = cls._mask_value(header_key, base_headers.get(header_key))
                logging.info("base_headers['%s'] = %s", header_key, masked)

        full_config = env.get_full_config()
        observed_keys = [
            "websocket_approval_key",
            "stock_account_number",
            "using_url",
            "is_paper_trading",
            "api_key",
            "api_secret_key",
            "paper_api_key",
            "paper_api_secret_key",
        ]
        for key in observed_keys:
            masked = cls._mask_value(key, full_config.get(key))
            logging.info("env.config['%s'] = %s", key, masked)

        token_manager_info = getattr(env, "token_manager", None)
        if token_manager_info is not None:
            storage_path = getattr(token_manager_info, "token_file_path", None)
            logging.info("TokenManager 저장 경로: %s", storage_path or "<알 수 없음>")

    @staticmethod
    def _mask_value(key: str, value: Any) -> str:
        """민감 정보는 앞/뒤 일부만 보이도록 마스킹한다."""
        if value is None:
            return "<None>"
        if isinstance(value, bool):
            return "True" if value else "False"
        if isinstance(value, (int, float)):
            return str(value)

        text = str(value)
        lower_key = key.lower()
        should_mask = any(marker in lower_key for marker in ("key", "secret", "token", "account", "pwd", "pass"))
        if not should_mask:
            return text if text else "<빈 문자열>"
        if len(text) <= 6:
            return "***"
        prefix = text[:4]
        suffix = text[-2:]
        return f"{prefix}...{suffix}"


class KoreaInvestAPISmokeTests(BaseKoreaInvestAPITest):
    """Live API smoke tests (safe read-only endpoints)."""

    STOCK_CODE = os.getenv("KI_TEST_STOCK_CODE", "005930")  # 삼성전자 기본값
    INDEX_MARKET = os.getenv("KI_TEST_INDEX_MARKET", "U")    # U: KOSPI, J: KOSDAQ
    INDEX_CODE = os.getenv("KI_TEST_INDEX_CODE", "0001")     # KOSPI 지수 코드

    def test_get_current_price(self) -> None:
        self.assertIsNotNone(self.api, "API 인스턴스가 초기화되지 않았습니다.")
        data = self.api.get_current_price(self.STOCK_CODE)
        self._print_raw("get_current_price", data)
        if not data:
            self.skipTest("현재가 데이터가 비어있습니다. 종목 코드 또는 장 상태를 확인하세요.")
        self.assertIn("stck_prpr", data)

    def test_get_minute_chart_data(self) -> None:
        self.assertIsNotNone(self.api)
        df = self.api.get_minute_chart_data(self.STOCK_CODE, start_time="090000", max_count=60)
        self._print_raw("get_minute_chart_data", df)
        if df is None or (pd is not None and df.empty):
            self.skipTest("분봉 데이터가 없습니다. 장 시간인지 확인하세요.")
        if pd is not None:
            self.assertGreater(len(df), 0)

    def test_get_index_current_price(self) -> None:
        self.assertIsNotNone(self.api)
        data = self.api.get_index_current_price(self.INDEX_MARKET, self.INDEX_CODE)
        self._print_raw("get_index_current_price", data)
        if not data or not data.get("output"):
            self.skipTest("지수 데이터가 없습니다. 시장/코드를 확인하세요.")
        self.assertTrue(data.get("ok"), data.get("meta"))

    def test_get_daily_price_chart(self) -> None:
        self.assertIsNotNone(self.api)
        end = datetime.now()
        start = end - timedelta(days=5)
        df = self.api.get_daily_price_chart(
            self.STOCK_CODE,
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            period_code="D",
        )
        self._print_raw("get_daily_price_chart", df)
        if df is None or (pd is not None and df.empty):
            self.skipTest("일봉 데이터가 없습니다. 종목/기간을 확인하세요.")
        if pd is not None:
            self.assertGreater(len(df), 0)


class KoreaInvestAccountScopedTests(BaseKoreaInvestAPITest):
    """계좌 정보가 필요한 API (환경에 따라 skip 가능)."""

    def test_get_account_balance(self) -> None:
        self.assertIsNotNone(self.api)
        response = self.api.get_acct_balance()
        self._handle_api_response("get_acct_balance", response)

    def test_get_orderable_amount(self) -> None:
        self.assertIsNotNone(self.api)
        stock_code = os.getenv("KI_TEST_STOCK_CODE", "005930")
        sample_price = int(os.getenv("KI_TEST_SAMPLE_PRICE", "70000"))
        data = self.api.get_orderable_amount(stock_code, sample_price)
        self._print_raw("get_orderable_amount", data)
        if not data:
            self.skipTest("주문가능 수량 데이터가 없습니다. 계좌 권한을 확인하세요.")
        self.assertIn("ord_psbl_qty", data)


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
