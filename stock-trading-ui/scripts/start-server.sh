#!/bin/bash

# ==========================================
# Next.js Frontend 서버 시작 스크립트
# ==========================================
# 사용법:
#   ./scripts/start-server.sh        (scripts 폴더에서)
#   ./stock-trading-ui/scripts/start-server.sh  (프로젝트 루트에서)
# ==========================================

set -e  # 에러 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 기본 설정
DEFAULT_PORT=9000
FRONTEND_NAME="Next.js Frontend"
FIXED_PORT=9000  # 포트를 9000번으로 고정

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

# 스크립트 실행 위치 감지 및 프론트엔드 디렉토리로 이동
find_frontend_dir() {
    local current_dir=$(pwd)

    # Case 1: scripts 폴더에서 실행
    if [[ "$current_dir" == *"/stock-trading-ui/scripts" ]]; then
        cd ..
        log_info "scripts 폴더에서 실행됨 - 상위 디렉토리로 이동"

    # Case 2: stock-trading-ui 폴더에서 실행
    elif [[ "$current_dir" == *"/stock-trading-ui" ]]; then
        log_info "stock-trading-ui 폴더에서 실행됨"

    # Case 3: 프로젝트 루트에서 실행
    elif [[ -d "stock-trading-ui" ]]; then
        cd stock-trading-ui
        log_info "프로젝트 루트에서 실행됨 - stock-trading-ui로 이동"

    # Case 4: 기타 위치
    else
        log_error "stock-trading-ui 디렉토리를 찾을 수 없습니다."
        log_error "다음 위치에서 실행해주세요:"
        log_error "  1. 프로젝트 루트 디렉토리"
        log_error "  2. stock-trading-ui 디렉토리"
        log_error "  3. stock-trading-ui/scripts 디렉토리"
        exit 1
    fi

    # package.json 존재 확인
    if [[ ! -f "package.json" ]]; then
        log_error "package.json을 찾을 수 없습니다. Next.js 프로젝트가 아닙니다."
        exit 1
    fi

    log_success "Frontend 디렉토리 확인: $(pwd)"
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

# 포트에서 실행 중인 프로세스 종료
kill_port_process() {
    local port=$1
    log_warning "포트 $port에서 실행 중인 프로세스를 종료합니다..."

    if command -v lsof >/dev/null 2>&1; then
        # lsof 사용
        local pids=$(lsof -ti :$port)
        if [[ -n "$pids" ]]; then
            echo $pids | xargs kill -9
            log_success "포트 $port의 프로세스들을 종료했습니다."
        fi
    elif command -v netstat >/dev/null 2>&1 && command -v awk >/dev/null 2>&1; then
        # netstat + awk 사용 (Linux)
        local pids=$(netstat -tulnp | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | grep -v '-')
        if [[ -n "$pids" ]]; then
            echo $pids | xargs kill -9
            log_success "포트 $port의 프로세스들을 종료했습니다."
        fi
    else
        log_error "포트 $port에서 실행 중인 프로세스를 자동으로 종료할 수 없습니다."
        log_error "수동으로 종료 후 다시 시도해주세요."
        exit 1
    fi

    # 잠시 대기 (프로세스 종료 완료 대기)
    sleep 2
}

# Node.js 및 npm 설치 확인
check_dependencies() {
    log_info "의존성 확인 중..."

    # Node.js 확인
    if ! command -v node >/dev/null 2>&1; then
        log_error "Node.js가 설치되지 않았습니다."
        log_error "Node.js를 설치한 후 다시 시도해주세요: https://nodejs.org/"
        exit 1
    fi

    # npm 확인
    if ! command -v npm >/dev/null 2>&1; then
        log_error "npm이 설치되지 않았습니다."
        log_error "npm을 설치한 후 다시 시도해주세요."
        exit 1
    fi

    local node_version=$(node --version)
    local npm_version=$(npm --version)

    log_success "Node.js: $node_version"
    log_success "npm: $npm_version"
}

# npm 의존성 설치
install_dependencies() {
    log_info "npm 의존성 확인 중..."

    if [[ ! -d "node_modules" ]] || [[ ! -f "node_modules/.package-lock.json" ]]; then
        log_warning "node_modules가 없거나 오래되었습니다. npm install을 실행합니다..."
        npm install
        log_success "의존성 설치 완료"
    else
        log_success "의존성이 이미 설치되어 있습니다."
    fi
}

# 개발 서버 시작
start_server() {
    # 포트를 9000번으로 고정
    local port=$FIXED_PORT

    log_info "$FRONTEND_NAME 서버를 포트 $port에서 시작합니다..."

    # 포트 충돌 확인 및 자동 처리
    if check_port $port; then
        log_warning "포트 $port가 이미 사용 중입니다. 기존 프로세스를 자동으로 종료합니다..."
        kill_port_process $port
        
        # 잠시 대기 후 다시 확인
        sleep 2
        if check_port $port; then
            log_error "포트 $port의 프로세스를 종료할 수 없습니다. 수동으로 종료 후 다시 시도해주세요."
            exit 1
        else
            log_success "포트 $port가 해제되었습니다."
        fi
    fi

    # 환경 변수 설정
    export PORT=$port
    export NODE_ENV=development
    
    # WSL 환경에서 Windows CMD 실행 방지
    if [[ "$WSL_DISTRO_NAME" != "" ]] || [[ -n "$WSLENV" ]] || [[ -n "$WSL_INTEROP" ]]; then
        log_info "WSL 환경에서 실행 중입니다."
        
        # WSL 환경에서 Node.js 직접 실행
        if command -v node >/dev/null 2>&1; then
            log_info "Node.js 직접 실행으로 Next.js 서버를 시작합니다..."
            
            log_info "서버 시작 중..."
            log_info "브라우저에서 http://localhost:$port 에 접속하세요"
            
            # WSL 환경에서 안전하게 Next.js 실행
            # npm/npx 대신 node를 직접 사용하여 실행
            local node_path=$(which node)
            local next_js_path="./node_modules/next/dist/bin/next"
            
            if [[ -f "$next_js_path" ]]; then
                log_info "Next.js를 직접 실행합니다: $node_path $next_js_path"
                exec "$node_path" "$next_js_path" dev --port $port --turbopack --hostname 0.0.0.0
            else
                log_error "Next.js 바이너리를 찾을 수 없습니다: $next_js_path"
                exit 1
            fi
        else
            log_error "Node.js를 찾을 수 없습니다."
            exit 1
        fi
    else
        # 일반 Linux/macOS 환경
        log_info "일반 환경에서 실행 중입니다."

        log_info "서버 시작 중..."
        log_info "브라우저에서 http://localhost:$port 에 접속하세요"

        # Next.js 개발 서버 시작
        exec npm run dev
    fi
}

# 메인 실행 함수
main() {
    echo "=========================================="
    echo "  $FRONTEND_NAME 서버 시작 스크립트"
    echo "=========================================="

    # 1. 프론트엔드 디렉토리 찾기 및 이동
    find_frontend_dir

    # 2. 의존성 확인
    check_dependencies

    # 3. npm 의존성 설치
    install_dependencies

    # 4. 서버 시작 (포트 9000 고정)
    start_server
}

# 도움말 출력
show_help() {
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  -h, --help  이 도움말을 출력"
    echo ""
    echo "설명:"
    echo "  Frontend 서버는 포트 9000번으로 고정 실행됩니다."
    echo "  기존 포트 9000을 사용하는 프로세스는 자동으로 종료됩니다."
    echo ""
    echo "예시:"
    echo "  $0          # 포트 9000에서 시작 (기존 프로세스 자동 종료)"
    echo ""
    echo "실행 위치:"
    echo "  - 프로젝트 루트에서: ./stock-trading-ui/scripts/start-server.sh"
    echo "  - stock-trading-ui에서: ./scripts/start-server.sh"
    echo "  - scripts 폴더에서: ./start-server.sh"
}

# 인자 처리
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    "")
        main
        ;;
    *)
        log_warning "포트 번호 인자는 더 이상 지원되지 않습니다. 포트 9000번으로 고정 실행됩니다."
        log_info "도움말을 보려면 '$0 --help'를 실행하세요."
        main
        ;;
esac