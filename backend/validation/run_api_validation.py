
import requests
import json
import os
import sys
from datetime import datetime

# 프로젝트 루트 경로를 sys.path에 추가
# 이 스크립트가 /backend/validation/에 있으므로, 두 단계 위로 올라가야 합니다.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

class APITestClient:
    """
    Backend API를 테스트하기 위한 클라이언트 클래스.
    실행중인 FastAPI 서버에 실제 HTTP 요청을 보냅니다.
    """
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        print(f"✅ Test Client Initialized. Target Server: {self.base_url}")

    def test_fetch_minute_data_by_date(self, stock_code, date_str):
        """
        특정 날짜의 분봉 데이터를 요청하고, 캐시 파일 생성 및 데이터 유효성을 검증합니다.
        """
        print("\n" + "="*50)
        print(f"▶️ STARTING TEST: Fetch minute data for {stock_code} on {date_str}")
        print("="*50)

        # 1. 목표 파일 경로 설정 및 사전 확인
        target_filename = f"{date_str.replace('-', '')}.json"
        target_dir = os.path.join(project_root, "kordata", stock_code)
        target_filepath = os.path.join(target_dir, target_filename)
        
        print(f"ℹ️ Target cache file: {target_filepath}")

        if os.path.exists(target_filepath):
            print(f"⚠️ Warning: Target file already exists. Deleting for a clean test.")
            os.remove(target_filepath)

        # 2. API 호출
        api_url = f"{self.base_url}/api/chart/{stock_code}/minute?date={date_str}"
        print(f"📡 Calling API: GET {api_url}")
        
        try:
            response = requests.get(api_url, timeout=180) # 타임아웃을 3분으로 넉넉하게 설정
        except requests.exceptions.RequestException as e:
            print(f"❌ FAILURE: API call failed. Error: {e}")
            return False

        # 3. 응답 코드 확인
        if response.status_code != 200:
            print(f"❌ FAILURE: API call returned status code {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
        
        print(f"✅ SUCCESS: API call returned status 200 OK.")

        # 4. 파일 생성 검증
        print(f"🔍 Verifying file creation...")
        if not os.path.exists(target_filepath):
            print(f"❌ FAILURE: Cache file was not created at {target_filepath}")
            return False
        
        print(f"✅ SUCCESS: Cache file created successfully.")

        # 5. 데이터 내용 검증
        print("🔍 Verifying file content...")
        try:
            with open(target_filepath, 'r', encoding='utf-8') as f:
                new_data = json.load(f)
            
            if not new_data:
                print("❌ FAILURE: New data file is empty.")
                return False

            # 비교를 위해 10월 2일 데이터 로드
            comparison_filepath = os.path.join(target_dir, "20251002.json")
            if not os.path.exists(comparison_filepath):
                print(f"⚠️ Warning: Comparison file not found at {comparison_filepath}. Skipping data comparison.")
            else:
                with open(comparison_filepath, 'r', encoding='utf-8') as f:
                    comp_data = json.load(f)
                
                # 첫 번째 캔들의 종가 비교
                new_first_candle_close = new_data[0].get('close')
                comp_first_candle_close = comp_data[0].get('close')

                if new_first_candle_close == comp_first_candle_close:
                    print(f"❌ FAILURE: Data for {date_str} seems identical to 2025-10-02.")
                    print(f"   - 10/01 09:00 Close: {new_first_candle_close}")
                    print(f"   - 10/02 09:00 Close: {comp_first_candle_close}")
                    return False
                
                print("✅ SUCCESS: Data content is different from comparison file.")
                print(f"   - {date_str} 09:00 Close: {new_first_candle_close}")
                print(f"   - 2025-10-02 09:00 Close: {comp_first_candle_close}")

            print("\n" + "-"*20 + " Fetched Data Sample " + "-"*20)
            for i, candle in enumerate(new_data[:3]):
                print(f"  [{i}] Timestamp: {candle.get('timestamp')}, Open: {candle.get('open')}, High: {candle.get('high')}, Low: {candle.get('low')}, Close: {candle.get('close')}, Volume: {candle.get('volume')}")
            print("-"*63)

        except Exception as e:
            print(f"❌ FAILURE: Error while verifying file content. Error: {e}")
            return False

        print("\n🎉 TEST COMPLETED SUCCESSFULLY! 🎉")
        return True

if __name__ == "__main__":
    # --- 테스트 설정 ---
    STOCK_CODE_TO_TEST = "005930"
    DATE_TO_TEST = "2025-10-01"
    
    # 백엔드 서버가 실행 중이어야 합니다.
    client = APITestClient(base_url="http://localhost:8000")
    
    # 테스트 실행
    success = client.test_fetch_minute_data_by_date(
        stock_code=STOCK_CODE_TO_TEST,
        date_str=DATE_TO_TEST
    )
    
    print("\n" + "="*50)
    if success:
        print("✅ FINAL RESULT: All tests passed.")
    else:
        print("❌ FINAL RESULT: One or more tests failed.")
    print("="*50)
