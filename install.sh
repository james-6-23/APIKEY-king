#!/usr/bin/env bash
# APIKEY-king · one-shot installer (docker-compose based)
#
# Usage:
#   bash <(curl -sSL https://raw.githubusercontent.com/james-6-23/APIKEY-king/main/install.sh)
#
# Interactive prompts:
#   · 安装目录     default: $HOME/apikey-king
#   · 监听端口     default: 8000 (auto-detects conflicts and re-prompts)
#   · 管理员密码   default: kyx200328
#
# The installer writes a standalone docker-compose.yml into the install
# directory and launches the service via `docker compose` (v2 plugin) or
# `docker-compose` (v1) — whichever is available.

set -euo pipefail

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────
readonly IMAGE='ghcr.io/james-6-23/apikey-king:latest'
readonly CONTAINER='apikey-king'
readonly DEFAULT_PORT='8000'
readonly DEFAULT_PASSWORD='kyx200328'
readonly DEFAULT_DIR="${HOME}/apikey-king"

readonly RED=$'\033[0;31m'
readonly GREEN=$'\033[0;32m'
readonly YELLOW=$'\033[1;33m'
readonly BLUE=$'\033[0;34m'
readonly DIM=$'\033[2m'
readonly BOLD=$'\033[1m'
readonly NC=$'\033[0m'

# ──────────────────────────────────────────────────────────────
# TTY resolution — `curl | bash` gives us an occupied stdin, so we read
# from /dev/tty directly whenever it's available.
# ──────────────────────────────────────────────────────────────
if [ -t 0 ]; then
    TTY=/dev/stdin
elif [ -r /dev/tty ]; then
    TTY=/dev/tty
else
    TTY=
fi

# COMPOSE_CMD filled by detect_compose below, used as a bash array
COMPOSE_CMD=()

# ──────────────────────────────────────────────────────────────
# Pretty-print helpers
# ──────────────────────────────────────────────────────────────
info()    { printf "${BLUE}›${NC} %s\n" "$*"; }
ok()      { printf "${GREEN}✓${NC} %s\n" "$*"; }
warn()    { printf "${YELLOW}!${NC} %s\n" "$*"; }
err()     { printf "${RED}✗${NC} %s\n" "$*" >&2; }
die()     { err "$@"; exit 1; }

banner() {
    printf "${BOLD}"
    cat <<'B'
 ┌──────────────────────────────────────────────────────┐
 │  > apikey-king :: surveillance console               │
 │    one-shot installer · docker-compose               │
 └──────────────────────────────────────────────────────┘
B
    printf "${NC}"
}

# ──────────────────────────────────────────────────────────────
# Prompt helpers — all reads go through $TTY so piped stdin is ok.
# ──────────────────────────────────────────────────────────────
prompt() {
    local question="$1" default="${2:-}" answer=""
    if [ -n "$default" ]; then
        printf "${BLUE}?${NC} %s ${DIM}[%s]${NC}: " "$question" "$default" >&2
    else
        printf "${BLUE}?${NC} %s: " "$question" >&2
    fi
    if [ -n "$TTY" ]; then
        IFS= read -r answer <"$TTY" || answer=""
    else
        IFS= read -r answer || answer=""
    fi
    printf '%s' "${answer:-$default}"
}

prompt_secret() {
    local question="$1" default="${2:-}" answer=""
    printf "${BLUE}?${NC} %s ${DIM}[enter=默认]${NC}: " "$question" >&2
    if [ -n "$TTY" ]; then
        IFS= read -rs answer <"$TTY" || answer=""
    else
        IFS= read -rs answer || answer=""
    fi
    printf '\n' >&2
    printf '%s' "${answer:-$default}"
}

confirm() {
    local question="$1" default="${2:-n}" answer hint
    if [ "$default" = "y" ]; then hint="Y/n"; else hint="y/N"; fi
    answer=$(prompt "$question [$hint]" "$default")
    case "${answer,,}" in
        y|yes) return 0 ;;
        *)     return 1 ;;
    esac
}

# ──────────────────────────────────────────────────────────────
# Environment checks
# ──────────────────────────────────────────────────────────────
check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        err "未检测到 docker 命令"
        echo  "请先安装 docker：https://docs.docker.com/engine/install/"
        echo  "或使用 curl -fsSL https://get.docker.com | sh  （Linux 快速安装）"
        exit 1
    fi
    if ! docker info >/dev/null 2>&1; then
        err "docker 无法访问（守护进程未运行 或 当前用户无权限）"
        echo  "Linux 把当前用户加进 docker 组： sudo usermod -aG docker \$USER  （然后重新登录）"
        echo  "macOS / Windows 检查 Docker Desktop 是否已启动"
        exit 1
    fi
}

detect_compose() {
    # Prefer the v2 plugin form: docker compose
    if docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD=(docker compose)
        return
    fi
    # Fallback to v1 standalone binary: docker-compose
    if command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD=(docker-compose)
        return
    fi
    err "未检测到 docker compose（plugin v2）或 docker-compose（v1）"
    echo  "推荐安装 docker compose plugin："
    echo  "  Debian/Ubuntu: sudo apt-get install -y docker-compose-plugin"
    echo  "  CentOS/RHEL:   sudo dnf install -y docker-compose-plugin"
    echo  "  或参考：       https://docs.docker.com/compose/install/"
    exit 1
}

# ──────────────────────────────────────────────────────────────
# Port conflict detection (best-effort across lsof / ss / netstat / docker)
# ──────────────────────────────────────────────────────────────
port_in_use() {
    local port="$1"
    if command -v lsof >/dev/null 2>&1; then
        lsof -iTCP:"$port" -sTCP:LISTEN -nP 2>/dev/null | grep -q LISTEN && return 0
    fi
    if command -v ss >/dev/null 2>&1; then
        ss -tlnH 2>/dev/null | awk '{print $4}' | grep -qE "[:.]${port}$" && return 0
    fi
    if command -v netstat >/dev/null 2>&1; then
        netstat -tln 2>/dev/null | awk '{print $4}' | grep -qE "[:.]${port}$" && return 0
    fi
    if docker ps --format '{{.Ports}}' 2>/dev/null | grep -qE "[:.]${port}->"; then
        return 0
    fi
    return 1
}

ask_port() {
    local port
    while :; do
        port=$(prompt "监听端口" "$DEFAULT_PORT")
        if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
            warn "端口号无效（需要 1–65535 的整数），请重新输入"
            continue
        fi
        if port_in_use "$port"; then
            warn "端口 ${port} 已被占用，请换一个"
            continue
        fi
        printf '%s' "$port"
        return
    done
}

ask_dir() {
    local d
    d=$(prompt "安装目录" "$DEFAULT_DIR")
    eval "d=\"$d\""   # Expand ~
    printf '%s' "$d"
}

ask_password() {
    local pw
    pw=$(prompt_secret "管理员密码" "$DEFAULT_PASSWORD")
    if [ -z "$pw" ]; then pw="$DEFAULT_PASSWORD"; fi
    if [ ${#pw} -lt 6 ]; then
        warn "密码少于 6 字符，使用默认值 ${DEFAULT_PASSWORD}"
        pw="$DEFAULT_PASSWORD"
    fi
    printf '%s' "$pw"
}

gen_secret() {
    if command -v openssl >/dev/null 2>&1; then
        openssl rand -hex 32
    else
        head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n'
    fi
}

# ──────────────────────────────────────────────────────────────
# Emit docker-compose.yml into the install directory
# ──────────────────────────────────────────────────────────────
write_compose() {
    local dir="$1" port="$2" password="$3" secret="$4"
    # Heredoc — single-quoted marker so ${} inside aren't expanded by bash,
    # we use envsubst-free string replacement via bash-level variables.
    cat > "${dir}/docker-compose.yml" <<COMPOSE
# Generated by install.sh on $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# Re-running the installer overwrites this file.

services:
  apikey-king:
    image: ${IMAGE}
    container_name: ${CONTAINER}
    restart: unless-stopped
    ports:
      - "${port}:8000"
    volumes:
      - ./data:/app/data
    environment:
      - TZ=Asia/Shanghai
      - APIKEY_KING_SECRET=${secret}
      - APIKEY_KING_DEFAULT_PASSWORD=${password}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
COMPOSE
    chmod 600 "${dir}/docker-compose.yml"   # contains secrets
}

# ──────────────────────────────────────────────────────────────
# Main flow
# ──────────────────────────────────────────────────────────────
main() {
    banner
    check_docker
    detect_compose

    local install_dir port password secret
    install_dir=$(ask_dir)
    port=$(ask_port)
    password=$(ask_password)
    secret=$(gen_secret)

    echo
    info "安装目录 : ${BOLD}${install_dir}${NC}"
    info "监听端口 : ${BOLD}${port}${NC}"
    info "初始密码 : ${BOLD}$(printf '%*s' ${#password} '' | tr ' ' '•')${NC} (${#password} chars)"
    info "JWT 密钥 : ${DIM}已随机生成 64 字节${NC}"
    info "Compose  : ${BOLD}${COMPOSE_CMD[*]}${NC}"
    echo

    if ! confirm "确认以上配置" "y"; then
        die "已取消"
    fi

    mkdir -p "${install_dir}/data"
    write_compose "$install_dir" "$port" "$password" "$secret"
    ok "docker-compose.yml 已生成 (mode 600)"

    info "拉取镜像 ${IMAGE} ..."
    ( cd "$install_dir" && "${COMPOSE_CMD[@]}" pull ) >/dev/null || die "拉取镜像失败"
    ok "镜像就绪"

    # Stop any existing container with the same name before re-launching
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER}\$"; then
        warn "发现同名容器 ${CONTAINER}，将停止并替换"
        ( cd "$install_dir" && "${COMPOSE_CMD[@]}" down ) >/dev/null 2>&1 || docker rm -f "$CONTAINER" >/dev/null || true
    fi

    info "启动服务..."
    ( cd "$install_dir" && "${COMPOSE_CMD[@]}" up -d ) >/dev/null
    ok "容器已启动"

    # Health-check wait loop
    info "等待服务就绪 (up to 60s) ..."
    local ready=0
    for _ in $(seq 1 60); do
        if curl -fsS "http://localhost:${port}/api/health" >/dev/null 2>&1; then
            ready=1
            break
        fi
        sleep 1
    done

    echo
    if [ "$ready" -eq 1 ]; then
        ok "服务已就绪 🚀"
    else
        warn "60s 内未通过健康检查，但容器已启动；请查看日志确认"
        echo  "  ${COMPOSE_CMD[*]} -f ${install_dir}/docker-compose.yml logs -f"
    fi

    # Detect accessible host (best-effort)
    local host_ip="localhost"
    if command -v hostname >/dev/null 2>&1; then
        local detected
        detected=$(hostname -I 2>/dev/null | awk '{print $1}') || true
        [ -n "${detected:-}" ] && host_ip="$detected"
    fi

    local cc="${COMPOSE_CMD[*]}"
    echo
    echo "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "${BOLD}  部署完成${NC}"
    echo "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo
    echo "  访问地址  ${BOLD}http://${host_ip}:${port}${NC}"
    echo "            ${DIM}http://localhost:${port}${NC}"
    echo "  初始密码  ${BOLD}${password}${NC}"
    echo "  数据目录  ${install_dir}/data  ${DIM}(持久化 · 重启不丢)${NC}"
    echo "  配置文件  ${install_dir}/docker-compose.yml  ${DIM}(含 secret · mode 600)${NC}"
    echo
    echo "${BOLD}常用命令${NC} ${DIM}(在 ${install_dir} 目录下执行)${NC}"
    echo "  实时日志  ${cc} logs -f"
    echo "  停止     ${cc} stop"
    echo "  启动     ${cc} start"
    echo "  重启     ${cc} restart"
    echo "  状态     ${cc} ps"
    echo "  更新     ${cc} pull && ${cc} up -d"
    echo "  卸载     ${cc} down && rm -rf ${install_dir}"
    echo
}

main "$@"
