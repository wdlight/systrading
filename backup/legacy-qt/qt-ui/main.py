# RSI/MACD 트레이딩 애플리케이션 메인 진입점
# 기존 rsimacd_trading.py에서 이동된 main 실행 부분

import sys
import yaml
from multiprocessing import Process, Queue
from PyQt5.QtWidgets import QApplication
from loguru import logger

# 새로운 구조의 모듈들 임포트
from brokers.korea_investment.ki_env import KoreaInvestEnv
from brokers.korea_investment.ki_api import KoreaInvestAPI
from ui.qt.main_window import KISAPIForm
from core.order_processor import send_tr_process

def main():
    """메인 애플리케이션 함수"""
    try:
        # 설정 파일 로드
        with open("./config.yaml", "r", encoding="UTF-8") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        
        logger.info("설정 파일 로드 완료")
        
        # 한국투자증권 환경 초기화
        env_cls = KoreaInvestEnv(config)
        base_headers = env_cls.get_base_headers()
        cfg = env_cls.get_full_config()
        
        # API 클라이언트 초기화
        korea_invest_api = KoreaInvestAPI(cfg, base_headers=base_headers)
        logger.info("API 클라이언트 초기화 완료")
        
        # 프로세스 간 통신용 큐 생성
        tr_req_queue = Queue()    # 주문 요청 큐
        tr_result_queue = Queue() # 주문 결과 큐
        
        logger.info("프로세스 간 통신 큐 생성 완료")
        
        # 주문 처리 프로세스 시작
        proc_order_tr = Process(
            target=send_tr_process, 
            args=(korea_invest_api, tr_req_queue, tr_result_queue)
        )
        proc_order_tr.start()
        logger.info("주문 처리 프로세스 시작")
        
        # PyQt5 애플리케이션 초기화
        app = QApplication(sys.argv)
        
        # 메인 윈도우 생성 및 표시
        main_app = KISAPIForm(
            korea_invest_api, 
            tr_req_queue, 
            tr_result_queue
        )
        main_app.show()
        logger.info("메인 윈도우 표시 완료")
        
        # 애플리케이션 실행
        logger.info("애플리케이션 시작")
        sys.exit(app.exec_())
        
    except FileNotFoundError as e:
        logger.error(f"설정 파일을 찾을 수 없습니다: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"설정 파일 파싱 오류: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"애플리케이션 실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()