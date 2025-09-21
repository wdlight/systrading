# 한국투자증권 토큰 관리자
# utils.py에서 이동된 TokenManager 클래스

import os
import json
import shutil
from datetime import datetime
from loguru import logger

class TokenManager:
    """토큰 파일 기반 관리 클래스"""
    
    def __init__(self, token_file="access.tok"):
        self.token_file = token_file
        self.backup_dir = "token_backup"
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def load_token_data(self):
        """토큰 파일에서 데이터 로드"""
        if not os.path.exists(self.token_file):
            return None
            
        try:
            with open(self.token_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"토큰 파일 로드 실패: {e}")
            return None
    
    def save_token_data(self, token_data):
        """토큰 데이터를 파일에 저장"""
        try:
            # 기존 파일이 있으면 백업
            if os.path.exists(self.token_file):
                self._backup_existing_token()
            
            # 새로운 토큰 데이터 저장
            token_data['last_updated'] = datetime.now().isoformat()
            with open(self.token_file, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"토큰 파일 저장 완료: {self.token_file}")
            return True
        except Exception as e:
            logger.error(f"토큰 파일 저장 실패: {e}")
            return False
    
    def _backup_existing_token(self):
        """기존 토큰 파일을 날짜별로 백업"""
        try:
            current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"access.{current_date}.tok"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            shutil.copy2(self.token_file, backup_path)
            logger.info(f"토큰 파일 백업 완료: {backup_path}")
        except Exception as e:
            logger.error(f"토큰 파일 백업 실패: {e}")
    
    def is_token_expired(self, hours_threshold=12):
        """토큰 파일의 생성 시간과 토큰 데이터를 기준으로 만료 여부 확인 (기본 12시간)"""
        if not os.path.exists(self.token_file):
            logger.info("토큰 파일이 존재하지 않음")
            return True
        
        try:
            # 토큰 데이터 로드
            token_data = self.load_token_data()
            if not token_data:
                logger.info("토큰 데이터 로드 실패")
                return True
            
            # last_updated 시간이 있으면 우선 사용
            if 'last_updated' in token_data:
                try:
                    last_updated = datetime.fromisoformat(token_data['last_updated'])
                    now = datetime.now()
                    elapsed_hours = (now - last_updated).total_seconds() / 3600
                    
                    logger.info(f"토큰 마지막 업데이트: {last_updated}")
                    logger.info(f"현재 시간: {now}")
                    logger.info(f"경과 시간: {elapsed_hours:.2f}시간")
                    
                    return elapsed_hours >= hours_threshold
                except ValueError as e:
                    logger.warning(f"last_updated 파싱 실패: {e}, 파일 수정시간으로 폴백")
            
            # last_updated가 없거나 파싱 실패 시 파일 수정시간 사용
            file_mtime = os.path.getmtime(self.token_file)
            file_time = datetime.fromtimestamp(file_mtime)
            now = datetime.now()
            elapsed_hours = (now - file_time).total_seconds() / 3600
            
            logger.info(f"토큰 파일 생성 시간: {file_time}")
            logger.info(f"현재 시간: {now}")
            logger.info(f"경과 시간: {elapsed_hours:.2f}시간")
            
            return elapsed_hours >= hours_threshold
        except Exception as e:
            logger.error(f"토큰 만료 시간 확인 실패: {e}")
            return True