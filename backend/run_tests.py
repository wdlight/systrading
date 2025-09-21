#!/usr/bin/env python3
"""
simple_server.py 테스트 실행 스크립트
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

def run_tests(test_type="all", verbose=True, coverage=False):
    """테스트 실행"""
    
    # 프로젝트 루트 디렉토리로 이동
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # pytest 실행 명령 구성
    cmd = ["python", "-m", "pytest"]
    
    if test_type == "simple_server":
        cmd.append("tests/test_simple_server.py")
    elif test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "api":
        cmd.extend(["-m", "api"])
    elif test_type == "websocket":
        cmd.extend(["-m", "websocket"])
    elif test_type == "all":
        cmd.append("tests/")
    else:
        cmd.append(f"tests/{test_type}")
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=term-missing", "--cov-report=html"])
    
    cmd.extend(["--tb=short", "--color=yes"])
    
    print(f"실행 명령: {' '.join(cmd)}")
    print("=" * 60)
    
    # 테스트 실행
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n테스트가 사용자에 의해 중단되었습니다.")
        return False
    except Exception as e:
        print(f"테스트 실행 중 오류 발생: {e}")
        return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="simple_server.py 테스트 실행")
    
    parser.add_argument(
        "test_type",
        nargs="?",
        default="simple_server",
        choices=["all", "simple_server", "unit", "api", "websocket"],
        help="실행할 테스트 타입"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=True,
        help="상세 출력"
    )
    
    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="코드 커버리지 측정"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="테스트 의존성 설치"
    )
    
    args = parser.parse_args()
    
    if args.install_deps:
        print("테스트 의존성 설치 중...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "pytest", "pytest-asyncio", "pytest-cov", "httpx"
        ])
        print("의존성 설치 완료")
        return
    
    print(f"🚀 {args.test_type} 테스트 시작")
    success = run_tests(
        test_type=args.test_type,
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    if success:
        print("✅ 모든 테스트 통과!")
        sys.exit(0)
    else:
        print("❌ 일부 테스트 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()