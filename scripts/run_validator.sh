#!/usr/bin/env bash
# =============================================================================
#  run_validator.sh
#  Orquestrador do Universal Code Validator
# =============================================================================
#
#  Responsabilidades:
#    1. Verificar pre-requisitos (Python, modulos, arquivos)
#    2. Executar o validador passando o alvo como argumento
#    3. Exibir o log gerado (texto + caminho do JSON)
#    4. Realizar rotacao de logs (retencao configuravel)
#    5. Retornar exit code adequado para integracao com CI/CD
#
#  Uso:
#    ./run_validator.sh <arquivo_ou_diretorio> [extensoes...]
#
#  Exemplos:
#    ./run_validator.sh MinhaClasse.java
#    ./run_validator.sh ./src .java .js .apex
#    ./run_validator.sh ./src .java --no-color
#
#  Variaveis de ambiente (opcionais):
#    VALIDATOR_AUTHOR      Nome do executor (default: $USER)
#    VALIDATOR_LOG_KEEP    Numero de logs a manter por rotacao (default: 10)
#    VALIDATOR_PYTHON      Caminho do Python (default: python3)
#    NO_COLOR              Desativa cores ANSI se definida
#
#  Autor   : Code Quality Guardian
#  Versao  : 2.0.0
#  Licenca : MIT
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuracoes globais
# ---------------------------------------------------------------------------

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly SCRIPT_VERSION="2.0.0"
readonly TOOL_NAME="Universal Code Validator"
readonly AUTHOR="${VALIDATOR_AUTHOR:-${USER:-unknown}}"
readonly LOG_DIR="${SCRIPT_DIR}/logs"
readonly LOG_KEEP="${VALIDATOR_LOG_KEEP:-10}"
readonly PYTHON="${VALIDATOR_PYTHON:-python3}"
readonly VALIDATOR_SCRIPT="${SCRIPT_DIR}/code_validator.py"
readonly LOGGER_MODULE="${SCRIPT_DIR}/validator_logger.py"
readonly RUN_TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
readonly RUN_DATE_FILE="$(date '+%Y%m%d_%H%M%S')"
readonly SHELL_LOG="${LOG_DIR}/shell_${RUN_DATE_FILE}.log"

# Cores ANSI (desativadas automaticamente se NO_COLOR estiver definida ou
# o stdout nao for um terminal)
if [[ -z "${NO_COLOR:-}" && -t 1 ]]; then
    RED='\033[0;91m';    GREEN='\033[0;92m';  YELLOW='\033[0;93m'
    CYAN='\033[0;96m';   BOLD='\033[1m';      RESET='\033[0m'
    GREY='\033[0;90m';   WHITE='\033[0;97m'
else
    RED=''; GREEN=''; YELLOW=''; CYAN=''; BOLD=''; RESET=''; GREY=''; WHITE=''
fi

# ---------------------------------------------------------------------------
# Funcoes utilitarias de log do shell
# ---------------------------------------------------------------------------

_ts() { date '+%Y-%m-%d %H:%M:%S'; }

log_info() {
    local msg="$*"
    echo -e "${WHITE}[$(_ts)] [INFO ]  ${msg}${RESET}"
    echo "[$(_ts)] [INFO ]  ${msg}" >> "${SHELL_LOG}"
}

log_ok() {
    local msg="$*"
    echo -e "${GREEN}[$(_ts)] [OK   ]  ${msg}${RESET}"
    echo "[$(_ts)] [OK   ]  ${msg}" >> "${SHELL_LOG}"
}

log_warn() {
    local msg="$*"
    echo -e "${YELLOW}[$(_ts)] [WARN ]  ${msg}${RESET}"
    echo "[$(_ts)] [WARN ]  ${msg}" >> "${SHELL_LOG}"
}

log_error() {
    local msg="$*"
    echo -e "${RED}[$(_ts)] [ERROR]  ${msg}${RESET}" >&2
    echo "[$(_ts)] [ERROR]  ${msg}" >> "${SHELL_LOG}"
}

log_section() {
    local title="$*"
    echo -e "\n${CYAN}${BOLD}  ── ${title}${RESET}"
    echo "" >> "${SHELL_LOG}"
    echo "  ── ${title}" >> "${SHELL_LOG}"
}

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

print_banner() {
    echo -e "${CYAN}${BOLD}"
    echo "  ╔════════════════════════════════════════════════════════════════════╗"
    echo "  ║   🔍  ${TOOL_NAME}                     ║"
    echo "  ║   Shell Orchestrator v${SCRIPT_VERSION}                                    ║"
    echo "  ╚════════════════════════════════════════════════════════════════════╝"
    echo -e "${RESET}"
    echo -e "${GREY}"
    echo "  Executor    : ${AUTHOR}"
    echo "  Data/Hora   : ${RUN_TIMESTAMP}"
    echo "  Host        : $(hostname)"
    echo "  SO          : $(uname -srm)"
    echo "  Python      : $(${PYTHON} --version 2>&1 || echo 'nao encontrado')"
    echo "  Diretorio   : ${SCRIPT_DIR}"
    echo "  Log Shell   : ${SHELL_LOG}"
    echo -e "${RESET}"

    # Tambem grava no log de shell
    {
        echo "======================================================================"
        echo "  ${TOOL_NAME} — Shell Orchestrator v${SCRIPT_VERSION}"
        echo "======================================================================"
        echo "  Executor    : ${AUTHOR}"
        echo "  Data/Hora   : ${RUN_TIMESTAMP}"
        echo "  Host        : $(hostname)"
        echo "  SO          : $(uname -srm)"
        echo "  Python      : $(${PYTHON} --version 2>&1 || echo 'nao encontrado')"
        echo "  Diretorio   : ${SCRIPT_DIR}"
        echo "======================================================================"
    } >> "${SHELL_LOG}"
}

# ---------------------------------------------------------------------------
# Pre-requisitos
# ---------------------------------------------------------------------------

check_prerequisites() {
    log_section "Verificando pre-requisitos"

    # Python disponivel?
    if ! command -v "${PYTHON}" &>/dev/null; then
        log_error "Python nao encontrado. Instale Python 3.8+ ou defina VALIDATOR_PYTHON."
        exit 1
    fi
    log_ok "Python : $(${PYTHON} --version 2>&1)"

    # Versao minima Python 3.8
    local py_ver
    py_ver="$(${PYTHON} -c 'import sys; print(sys.version_info[:2])')"
    local py_major py_minor
    py_major="$(${PYTHON} -c 'import sys; print(sys.version_info.major)')"
    py_minor="$(${PYTHON} -c 'import sys; print(sys.version_info.minor)')"
    if [[ "${py_major}" -lt 3 ]] || [[ "${py_major}" -eq 3 && "${py_minor}" -lt 8 ]]; then
        log_error "Python 3.8+ necessario. Versao atual: ${py_ver}"
        exit 1
    fi

    # Arquivos do validador
    if [[ ! -f "${VALIDATOR_SCRIPT}" ]]; then
        log_error "Arquivo nao encontrado: ${VALIDATOR_SCRIPT}"
        exit 1
    fi
    log_ok "Modulo principal : ${VALIDATOR_SCRIPT}"

    if [[ ! -f "${LOGGER_MODULE}" ]]; then
        log_error "Arquivo nao encontrado: ${LOGGER_MODULE}"
        exit 1
    fi
    log_ok "Modulo logger    : ${LOGGER_MODULE}"

    # Modulo uuid (stdlib)
    if ! ${PYTHON} -c "import uuid, socket, platform" &>/dev/null; then
        log_error "Modulos stdlib ausentes (uuid, socket, platform). Verifique a instalacao do Python."
        exit 1
    fi
    log_ok "Modulos stdlib   : ok"
}

# ---------------------------------------------------------------------------
# Validacao dos argumentos
# ---------------------------------------------------------------------------

validate_arguments() {
    local target="$1"

    log_section "Validando argumentos"

    if [[ -z "${target}" ]]; then
        log_error "Nenhum alvo especificado."
        usage
        exit 1
    fi

    if [[ ! -e "${target}" ]]; then
        log_error "Alvo nao existe: ${target}"
        exit 1
    fi

    log_ok "Alvo : ${target}"
}

# ---------------------------------------------------------------------------
# Rotacao de logs
# ---------------------------------------------------------------------------

rotate_logs() {
    log_section "Rotacao de logs (retencao: ${LOG_KEEP} arquivos por tipo)"

    mkdir -p "${LOG_DIR}"

    for pattern in "validator_*.log" "validator_*.json" "shell_*.log"; do
        local files
        # Lista arquivos ordenados por data de modificacao (mais antigos primeiro)
        mapfile -t files < <(ls -t "${LOG_DIR}"/${pattern} 2>/dev/null || true)
        local total="${#files[@]}"

        if [[ "${total}" -gt "${LOG_KEEP}" ]]; then
            local to_delete=$(( total - LOG_KEEP ))
            log_info "Removendo ${to_delete} log(s) antigo(s) do padrao '${pattern}'"
            for (( i = LOG_KEEP; i < total; i++ )); do
                rm -f "${files[$i]}"
                log_info "  Removido: ${files[$i]}"
            done
        else
            log_ok "Padrao '${pattern}': ${total}/${LOG_KEEP} — sem remocao necessaria"
        fi
    done
}

# ---------------------------------------------------------------------------
# Exibicao do log gerado pelo Python
# ---------------------------------------------------------------------------

display_python_log() {
    local latest_log
    latest_log="$(ls -t "${LOG_DIR}"/validator_*.log 2>/dev/null | head -1 || echo '')"

    if [[ -z "${latest_log}" ]]; then
        log_warn "Nenhum log Python encontrado em ${LOG_DIR}"
        return
    fi

    log_section "Log de execucao das regras — ${latest_log}"
    echo ""
    # Exibe com numeracao de linha para facilitar leitura
    if command -v awk &>/dev/null; then
        awk '{printf "  %4d | %s\n", NR, $0}' "${latest_log}"
    else
        cat "${latest_log}"
    fi
    echo ""
    echo "${SHELL_LOG}" >> "${SHELL_LOG}" 2>/dev/null || true
}

display_json_summary() {
    local latest_json
    latest_json="$(ls -t "${LOG_DIR}"/validator_*.json 2>/dev/null | head -1 || echo '')"

    if [[ -z "${latest_json}" ]]; then
        return
    fi

    log_section "Log estruturado (JSON) disponivel"
    log_info "Caminho : ${latest_json}"

    # Se python estiver disponivel, exibe resumo do JSON
    ${PYTHON} - "${latest_json}" <<'PYEOF'
import json, sys
path = sys.argv[1]
try:
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    print(f"\n  {'─'*60}")
    print(f"  {'Campo':<25} {'Valor'}")
    print(f"  {'─'*60}")
    fields = [
        ('session_id',        'session_id'),
        ('tool_version',      'tool_version'),
        ('author',            'author'),
        ('started_at',        'started_at'),
        ('finished_at',       'finished_at'),
        ('total_duration_ms', 'total_duration_ms'),
        ('target_path',       'target_path'),
        ('files_analyzed',    'files_analyzed'),
        ('total_violations',  'total_violations'),
        ('overall_status',    'overall_status'),
        ('aborted_at_rule',   'aborted_at_rule'),
    ]
    for label, key in fields:
        val = data.get(key, '')
        if val != '':
            print(f"  {label:<25} {val}")
    print(f"  {'─'*60}")
    rules = data.get('rules', [])
    if rules:
        print(f"\n  {'Regra':<8} {'Nome':<45} {'Status':<10} {'Violacoes':<10} {'ms'}")
        print(f"  {'─'*85}")
        for r in rules:
            aborted = ' <- ABORT' if r.get('aborted_chain') else ''
            print(
                f"  {r.get('rule_id',''):<8} "
                f"{r.get('rule_name','')[:43]:<45} "
                f"{r.get('status',''):<10} "
                f"{r.get('violations',0):<10} "
                f"{r.get('duration_ms',0):.1f}"
                f"{aborted}"
            )
    print()
except Exception as ex:
    print(f"  Nao foi possivel ler o JSON: {ex}")
PYEOF
}

# ---------------------------------------------------------------------------
# Execucao principal do validador
# ---------------------------------------------------------------------------

run_validator() {
    local target="$1"
    shift
    local extra_args=("$@")

    log_section "Executando validacao"
    log_info "Alvo         : ${target}"
    log_info "Argumentos   : ${extra_args[*]:-nenhum}"
    log_info "Comando      : ${PYTHON} ${VALIDATOR_SCRIPT} ${target} ${extra_args[*]:-}"
    echo "" >> "${SHELL_LOG}"

    local exit_code=0

    # Executa o validador Python; captura exit code sem disparar 'set -e'
    ${PYTHON} "${VALIDATOR_SCRIPT}" "${target}" "${extra_args[@]:-}" \
        2>> "${SHELL_LOG}" || exit_code=$?

    return "${exit_code}"
}

# ---------------------------------------------------------------------------
# Resultado final
# ---------------------------------------------------------------------------

print_result() {
    local exit_code="$1"

    log_section "Resultado final"

    if [[ "${exit_code}" -eq 0 ]]; then
        log_ok "Validacao concluida SEM violacoes. ✅"
        echo "[$(_ts)] [RESULT]  PASSED — sem violacoes" >> "${SHELL_LOG}"
    else
        log_warn "Validacao concluida COM violacoes ou pipeline abortado. ⚠️"
        echo "[$(_ts)] [RESULT]  FAILED — violacoes encontradas ou pipeline abortado" >> "${SHELL_LOG}"
    fi

    echo ""
    log_info "Log shell   : ${SHELL_LOG}"
    echo ""
}

# ---------------------------------------------------------------------------
# Uso
# ---------------------------------------------------------------------------

usage() {
    echo ""
    echo "Uso:"
    echo "  ${SCRIPT_NAME} <arquivo_ou_diretorio> [extensoes...]"
    echo ""
    echo "Exemplos:"
    echo "  ${SCRIPT_NAME} MinhaClasse.java"
    echo "  ${SCRIPT_NAME} ./src .java .js .apex"
    echo ""
    echo "Variaveis de ambiente:"
    echo "  VALIDATOR_AUTHOR   Nome do executor (default: \$USER)"
    echo "  VALIDATOR_LOG_KEEP Logs a manter por tipo (default: 10)"
    echo "  VALIDATOR_PYTHON   Caminho do Python (default: python3)"
    echo "  NO_COLOR           Desativa cores ANSI"
    echo ""
}

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

main() {
    # Garante existencia do diretorio de logs desde o inicio
    mkdir -p "${LOG_DIR}"
    # Cria o arquivo de log shell (touch cria vazio)
    : > "${SHELL_LOG}"

    if [[ $# -lt 1 ]]; then
        print_banner
        usage
        exit 1
    fi

    local target="$1"
    shift
    local extra_args=("$@")

    print_banner
    check_prerequisites
    validate_arguments "${target}"
    rotate_logs

    local validator_exit=0
    run_validator "${target}" "${extra_args[@]:-}" || validator_exit=$?

    display_python_log
    display_json_summary
    print_result "${validator_exit}"

    exit "${validator_exit}"
}

main "$@"
