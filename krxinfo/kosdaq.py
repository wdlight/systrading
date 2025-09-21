import pandas as pd
from rapidfuzz import process

# --- 데이터 로딩 ---
def load_stock_dict():
    """KRX 코스닥 상장 종목 dict 생성 (종목코드: 회사명)"""
    url = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13"
    df = pd.read_html(url, header=0)[0]
    df['종목코드'] = df['종목코드'].apply(lambda x: str(x).zfill(6))
    df = df[df['시장구분'] == 'KOSDAQ']   # ✅ 코스닥만 필터링
    return dict(zip(df['종목코드'], df['회사명']))

# 전역 종목 dict
STOCK_DICT = load_stock_dict()

# --- 검색 함수 ---
def find_stock_code(query: str, limit: int = 5):
    """
    종목명을 입력하면 유사도가 높은 코스닥 종목들을 찾아줌
    :param query: 검색할 문자열 (예: '셀트리온헬스케어', '에코프로')
    :param limit: 출력할 후보 개수
    :return: [(종목명, 종목코드, 유사도), ...]
    """
    results = process.extract(query, STOCK_DICT.values(), limit=limit)
    output = []
    for match, score, _ in results:
        code = [k for k, v in STOCK_DICT.items() if v == match][0]
        output.append((match, code, score))
    return output

# --- 단독 실행 시 동작 ---
if __name__ == "__main__":
    print("📌 코스닥 종목명 검색기 (유사도 기반)")
    while True:
        query = input("\n검색할 종목명을 입력하세요 (종료: q): ").strip()
        if query.lower() == "q":
            print("종료합니다.")
            break
        results = find_stock_code(query)
        if results:
            print("🔎 검색 결과:")
            for name, code, score in results:
                print(f" - {name} ({code}) | 유사도 {score:.1f}")
        else:
            print("❌ 해당하는 종목을 찾을 수 없습니다.")
