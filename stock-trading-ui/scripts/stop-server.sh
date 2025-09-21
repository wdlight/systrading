#!/bin/bash

# ==========================================
# Next.js Frontend 서버 종료 스크립트
# ==========================================
# 사용법:
#   ./scripts/stop-server.sh         (scripts 폴더에서)
#   ./stock-trading-ui/scripts/stop-server.sh  (프로젝트 루트에서)
# ==========================================

set -e  # 에러 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 기본 설정
DEFAULT_PORT=3000
FRONTEND_NAME="Next.js Frontend"

# 로그 함수들
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 포트 사용 여부 확인
check_port() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        return $(lsof -i :$port >/dev/null 2>&1; echo $?)
    elif command -v netstat >/dev/null 2>&1; then
        return $(netstat -tuln | grep ":$port " >/dev/null 2>&1; echo $?)
    elif command -v ss >/dev/null 2>&1; then
        return $(ss -tuln | grep ":$port " >/dev/null 2>&1; echo $?)
    else
        log_warning "포트 확인 도구(lsof, netstat, ss)를 찾을 수 없습니다."
        return 1
    fi
}

# 포트에서 실행 중인 프로세스 정보 조회
get_port_process_info() {
    local port=$1

    if command -v lsof >/dev/null 2>&1; then
        # lsof 사용 (가장 정확함)
        lsof -i :$port -P -n | grep LISTEN
    elif command -v netstat >/dev/null 2>&1; then
        # netstat 사용
        netstat -tulnp | grep ":$port "
    elif command -v ss >/dev/null 2>&1; then
        # ss 사용
        ss -tulnp | grep ":$port "
    else
        log_warning "프로세스 정보 조회 도구를 찾을 수 없습니다."
        return 1
    fi
}

# 포트에서 실행 중인 프로세스 종료
kill_port_process() {
    local port=$1
    local force=${2:-false}

    log_info "포트 $port에서 실행 중인 프로세스를 확인합니다..."

    # 프로세스 정보 표시
    local process_info=$(get_port_process_info $port)
    if [[ -n "$process_info" ]]; then
        echo "----------------------------------------"
        echo "포트 $port에서 실행 중인 프로세스:"
        echo "$process_info"
        echo "----------------------------------------"
    else
        log_info "포트 $port에서 실행 중인 프로세스가 없습니다."
        return 0
    fi

    # 사용자 확인 (force 옵션이 아닌 경우)
    if [[ "$force" != "true" ]]; then
        read -p "위 프로세스들을 종료하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "프로세스 종료가 취소되었습니다."
            return 1
        fi
    fi

    log_warning "포트 $port의 프로세스들을 종료합니다..."

    # PID 추출 및 종료
    local pids=""
    if command -v lsof >/dev/null 2>&1; then
        # lsof 사용
        pids=$(lsof -ti :$port)
    elif command -v netstat >/dev/null 2>&1 && command -v awk >/dev/null 2>&1; then
        # netstat + awk 사용 (Linux)
        pids=$(netstat -tulnp | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | grep -v '-' | tr '\n' ' ')
    elif command -v ss >/dev/null 2>&1 && command -v awk >/dev/null 2>&1; then
        # ss + awk 사용 (Linux)
        pids=$(ss -tulnp | grep ":$port " | awk '{print $6}' | cut -d',' -f2 | cut -d'=' -f2 | grep -v '-' | tr '\n' ' ')
    fi

    if [[ -n "$pids" ]]; then
        # 먼저 SIGTERM으로 정상 종료 시도
        log_info "정상 종료 신호(SIGTERM)를 보냅니다..."
        echo $pids | xargs kill -TERM 2>/dev/null || true

        # 3초 대기
        sleep 3

        # 여전히 실행 중인지 확인
        local remaining_pids=""
        for pid in $pids; do
            if kill -0 $pid 2>/dev/null; then
                remaining_pids="$remaining_pids $pid"
            fi
        done

        # 남은 프로세스가 있다면 강제 종료
        if [[ -n "$remaining_pids" ]]; then
            log_warning "일부 프로세스가 여전히 실행 중입니다. 강제 종료합니다..."
            echo $remaining_pids | xargs kill -9 2>/dev/null || true
            sleep 1
        fi

        log_success "포트 $port의 프로세스들을 종료했습니다."
    else
        log_warning "종료할 프로세스 ID를 찾을 수 없습니다."
    fi

    # 최종 확인
    sleep 1
    if check_port $port; then
        log_error "포트 $port의 프로세스 종료에 실패했습니다."
        return 1
    else
        log_success "포트 $port가 성공적으로 해제되었습니다."
        return 0
    fi
}

# 모든 Next.js 관련 프로세스 종료
kill_all_nextjs_processes() {
    log_info "모든 Next.js 관련 프로세스를 찾아 종료합니다..."

    # Next.js 프로세스 찾기
    local nextjs_pids=""
    if command -v pgrep >/dev/null 2>&1; then
        # pgrep 사용
        nextjs_pids=$(pgrep -f "next.*dev\|npm.*run.*dev\|yarn.*dev" 2>/dev/null || true)
    elif command -v ps >/dev/null 2>&1; then
        # ps + grep 사용
        nextjs_pids=$(ps aux | grep -E "next.*dev|npm.*run.*dev|yarn.*dev" | grep -v grep | awk '{print $2}' | tr '\n' ' ')
    fi

    if [[ -n "$nextjs_pids" ]]; then
        echo "----------------------------------------"
        echo "발견된 Next.js 관련 프로세스들:"
        if command -v ps >/dev/null 2>&1; then
            ps aux | grep -E "next.*dev|npm.*run.*dev|yarn.*dev" | grep -v grep
        fi
        echo "----------------------------------------"

        read -p "위 프로세스들을 모두 종료하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_warning "Next.js 프로세스들을 종료합니다..."
            echo $nextjs_pids | xargs kill -TERM 2>/dev/null || true
            sleep 2
            # 강제 종료가 필요한 경우
            echo $nextjs_pids | xargs kill -9 2>/dev/null || true
            log_success "Next.js 프로세스들을 종료했습니다."
        else
            log_info "프로세스 종료가 취소되었습니다."
        fi
    else
        log_info "실행 중인 Next.js 프로세스를 찾을 수 없습니다."
    fi
}

# 포트 스캔 (3000-3010 범위의 일반적인 개발 포트들)
scan_common_ports() {
    log_info "일반적인 개발 포트들을 스캔합니다..."

    local found_processes=false
    for port in {3000..3010}; do
        if check_port $port; then
            if [[ "$found_processes" == "false" ]]; then
                echo "=========================================="
                echo "사용 중인 포트들:"
                echo "=========================================="
                found_processes=true
            fi

            echo "포트 $port:"
            get_port_process_info $port | head -5
            echo "----------------------------------------"
        fi
    done

    if [[ "$found_processes" == "false" ]]; then
        log_success "3000-3010 포트 범위에서 실행 중인 프로세스가 없습니다."
    else
        echo ""
        read -p "위 포트들의 프로세스를 모두 종료하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            for port in {3000..3010}; do
                if check_port $port; then
                    kill_port_process $port true
                fi
            done
        fi
    fi
}

# 도움말 출력
show_help() {
    echo "사용법: $0 [옵션] [포트번호]"
    echo ""
    echo "옵션:"
    echo "  포트번호        특정 포트의 프로세스만 종료 (기본값: 3000)"
    echo "  -a, --all       모든 Next.js 관련 프로세스 종료"
    echo "  -s, --scan      일반적인 개발 포트 스캔 (3000-3010)"
    echo "  -f, --force     확인 없이 강제 종료"
    echo "  -h, --help      이 도움말을 출력"
    echo ""
    echo "예시:"
    echo "  $0              # 포트 3000의 프로세스 종료"
    echo "  $0 3001         # 포트 3001의 프로세스 종료"
    echo "  $0 -a           # 모든 Next.js 프로세스 종료"
    echo "  $0 -s           # 개발 포트 스캔"
    echo "  $0 -f 3000      # 포트 3000 강제 종료"
    echo ""
    echo "실행 위치:"
    echo "  - 프로젝트 루트에서: ./stock-trading-ui/scripts/stop-server.sh"
    echo "  - stock-trading-ui에서: ./scripts/stop-server.sh"
    echo "  - scripts 폴더에서: ./stop-server.sh"
}

# 메인 실행 함수
main() {
    echo "=========================================="
    echo "  $FRONTEND_NAME 서버 종료 스크립트"
    echo "=========================================="

    local target_port=$DEFAULT_PORT
    local force_mode=false
    local scan_mode=false
    local all_mode=false

    # 인자 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            -a|--all)
                all_mode=true
                shift
                ;;
            -s|--scan)
                scan_mode=true
                shift
                ;;
            -f|--force)
                force_mode=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -*)
                log_error "알 수 없는 옵션: $1"
                show_help
                exit 1
                ;;
            *)
                if [[ "$1" =~ ^[0-9]+$ ]] && [[ "$1" -ge 1024 ]] && [[ "$1" -le 65535 ]]; then
                    target_port=$1
                else
                    log_error "올바른 포트 번호를 입력해주세요 (1024-65535): $1"
                    exit 1
                fi
                shift
                ;;
        esac
    done

    # 모드별 실행
    if [[ "$all_mode" == "true" ]]; then
        kill_all_nextjs_processes
    elif [[ "$scan_mode" == "true" ]]; then
        scan_common_ports
    else
        # 특정 포트 종료
        if check_port $target_port; then
            kill_port_process $target_port $force_mode
        else
            log_info "포트 $target_port에서 실행 중인 프로세스가 없습니다."
        fi
    fi

    log_success "서버 종료 스크립트가 완료되었습니다."
}

# 스크립트 실행
main "$@"