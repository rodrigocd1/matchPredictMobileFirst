#!/usr/bin/env bash
# =============================================================================
#  setup-hooks.sh
#
#  Configura o ambiente local de desenvolvimento do projeto.
#  Execute UMA vez apos clonar o repositorio.
#
#  O que faz:
#    1. Verifica pre-requisitos (Git, Python)
#    2. Aponta o Git para a pasta .githooks/ deste repositorio
#    3. Garante permissao de execucao nos hooks
#    4. Configura o template de mensagem de commit (.gitmessage)
#    5. Valida que os arquivos obrigatorios existem
#    6. Exibe resumo completo da configuracao aplicada
#
#  Uso:
#    ./setup-hooks.sh
#
#  Autor   : Code Quality Guardian
#  Versao  : 2.0.0
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Variaveis globais
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="${SCRIPT_DIR}/.githooks"
GITMESSAGE_FILE="${SCRIPT_DIR}/.gitmessage"
PR_TEMPLATE_FILE="${SCRIPT_DIR}/.github/pull_request_template.md"
VALIDATOR_DIR="${SCRIPT_DIR}/tools/validator"

# ---------------------------------------------------------------------------
# Cores (desativadas se nao for terminal)
# ---------------------------------------------------------------------------

if [ -t 1 ]; then
    RED='\033[0;91m';    GREEN='\033[0;92m';  YELLOW='\033[0;93m'
    CYAN='\033[0;96m';   BOLD='\033[1m';      RESET='\033[0m'
    GREY='\033[0;90m'
else
    RED=''; GREEN=''; YELLOW=''; CYAN=''; BOLD=''; RESET=''; GREY=''
fi

# ---------------------------------------------------------------------------
# Funcoes utilitarias
# ---------------------------------------------------------------------------

step_ok()   { echo -e "${GREEN}  ✔  $*${RESET}"; }
step_warn() { echo -e "${YELLOW}  ⚠  $*${RESET}"; }
step_fail() { echo -e "${RED}  ✘  $*${RESET}"; }
step_info() { echo -e "      ${GREY}$*${RESET}"; }
section()   { echo -e "\n${CYAN}${BOLD}  ── $* ${RESET}"; }

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

print_banner() {
    echo ""
    echo -e "${CYAN}${BOLD}  ╔════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${CYAN}${BOLD}  ║   🔧  Setup de Ambiente — Code Quality Guardian           ║${RESET}"
    echo -e "${CYAN}${BOLD}  ║   Versao 2.0.0                                            ║${RESET}"
    echo -e "${CYAN}${BOLD}  ╚════════════════════════════════════════════════════════════╝${RESET}"
    echo ""
    echo -e "  ${GREY}Repositorio : ${SCRIPT_DIR}${RESET}"
    echo -e "  ${GREY}Executado em: $(date '+%d/%m/%Y %H:%M:%S')${RESET}"
    echo -e "  ${GREY}Executado por: ${USER:-unknown}${RESET}"
    echo ""
}

# ---------------------------------------------------------------------------
# Etapa 1 — Pre-requisitos
# ---------------------------------------------------------------------------

check_prerequisites() {
    section "Verificando pre-requisitos"

    # Git disponivel?
    if ! command -v git &>/dev/null; then
        step_fail "Git nao encontrado. Instale o Git antes de continuar."
        exit 1
    fi
    step_ok "Git : $(git --version)"

    # Dentro de um repositorio Git?
    if ! git -C "${SCRIPT_DIR}" rev-parse --git-dir > /dev/null 2>&1; then
        step_fail "Este diretorio nao e um repositorio Git: ${SCRIPT_DIR}"
        exit 1
    fi
    step_ok "Repositorio Git detectado"

    # Python disponivel?
    if command -v python3 &>/dev/null; then
        step_ok "Python : $(python3 --version 2>&1)"
    elif command -v python &>/dev/null; then
        step_ok "Python : $(python --version 2>&1)"
    else
        step_warn "Python nao encontrado. O validador de codigo nao funcionara localmente."
        step_info "Instale Python 3.8+ para usar: ./tools/validator/run_validator.sh"
    fi
}

# ---------------------------------------------------------------------------
# Etapa 2 — Git Hooks
# ---------------------------------------------------------------------------

configure_hooks() {
    section "Configurando Git Hooks"

    # Pasta .githooks existe?
    if [ ! -d "${HOOKS_DIR}" ]; then
        step_fail "Pasta .githooks nao encontrada em: ${HOOKS_DIR}"
        step_info "Verifique se o repositorio foi clonado corretamente."
        exit 1
    fi

    # Aplica permissao de execucao em todos os hooks
    chmod +x "${HOOKS_DIR}"/*
    step_ok "Permissoes de execucao aplicadas em .githooks/"

    # Aponta o Git para a pasta de hooks do projeto
    git -C "${SCRIPT_DIR}" config core.hooksPath .githooks
    step_ok "core.hooksPath = .githooks"
    step_info "O Git usara os hooks desta pasta em vez dos hooks globais."

    # Confirma hook commit-msg
    if [ -f "${HOOKS_DIR}/commit-msg" ]; then
        step_ok "Hook commit-msg encontrado e ativo"
        step_info "Todo 'git commit' sera validado automaticamente."
    else
        step_warn "Hook commit-msg nao encontrado em .githooks/"
        step_info "A validacao local de mensagens nao estara ativa."
    fi
}

# ---------------------------------------------------------------------------
# Etapa 3 — Template de mensagem de commit
# ---------------------------------------------------------------------------

configure_commit_template() {
    section "Configurando template de mensagem de commit"

    if [ ! -f "${GITMESSAGE_FILE}" ]; then
        step_warn "Arquivo .gitmessage nao encontrado em: ${GITMESSAGE_FILE}"
        step_info "O template de commit nao sera configurado."
        step_info "Crie o arquivo .gitmessage na raiz do repositorio."
        return
    fi

    # Configura o template para este repositorio (nao afeta config global)
    git -C "${SCRIPT_DIR}" config commit.template .gitmessage
    step_ok "commit.template = .gitmessage"
    step_info "Ao rodar 'git commit' (sem -m), o editor abrira com o template."
    step_info "Preencha a linha final e remova os comentarios (linhas com #)."

    # Exibe preview do template
    echo ""
    echo -e "  ${GREY}Preview do template:${RESET}"
    echo -e "  ${GREY}┌──────────────────────────────────────────────────────┐${RESET}"
    while IFS= read -r line; do
        echo -e "  ${GREY}│  ${line}${RESET}"
    done < "${GITMESSAGE_FILE}"
    echo -e "  ${GREY}└──────────────────────────────────────────────────────┘${RESET}"
}

# ---------------------------------------------------------------------------
# Etapa 4 — Validacao dos arquivos obrigatorios
# ---------------------------------------------------------------------------

validate_required_files() {
    section "Validando arquivos do projeto"

    local all_ok=true

    # Define os arquivos obrigatorios e suas descricoes
    declare -A REQUIRED_FILES
    REQUIRED_FILES["${HOOKS_DIR}/commit-msg"]="Hook Git de validacao de commit"
    REQUIRED_FILES["${GITMESSAGE_FILE}"]="Template de mensagem de commit"
    REQUIRED_FILES["${VALIDATOR_DIR}/code_validator.py"]="Motor de validacao de codigo"
    REQUIRED_FILES["${VALIDATOR_DIR}/validator_logger.py"]="Sistema de logging"
    REQUIRED_FILES["${VALIDATOR_DIR}/run_validator.sh"]="Orquestrador shell do validador"
    REQUIRED_FILES["${SCRIPT_DIR}/.github/workflows/commit-message-lint.yml"]="Workflow: lint de commits"
    REQUIRED_FILES["${SCRIPT_DIR}/.github/workflows/code-quality.yml"]="Workflow: qualidade de codigo"

    for filepath in "${!REQUIRED_FILES[@]}"; do
        description="${REQUIRED_FILES[$filepath]}"
        # Caminho relativo para exibicao
        relative="${filepath#${SCRIPT_DIR}/}"
        if [ -f "${filepath}" ]; then
            step_ok "${relative}"
            step_info "${description}"
        else
            step_warn "${relative} — NAO ENCONTRADO"
            step_info "${description}"
            all_ok=false
        fi
    done

    # PR Template e opcional — so avisa
    if [ -f "${PR_TEMPLATE_FILE}" ]; then
        step_ok ".github/pull_request_template.md"
        step_info "Template de Pull Request configurado"
    else
        step_warn ".github/pull_request_template.md — nao encontrado (opcional)"
        step_info "PRs nao terao template pre-preenchido na UI do GitHub"
    fi

    if [ "$all_ok" = false ]; then
        echo ""
        step_warn "Alguns arquivos obrigatorios estao ausentes."
        step_info "Verifique se o repositorio foi clonado corretamente"
        step_info "e se todos os arquivos foram commitados."
    fi
}

# ---------------------------------------------------------------------------
# Etapa 5 — Resumo final
# ---------------------------------------------------------------------------

print_summary() {
    echo ""
    echo -e "${CYAN}${BOLD}  ══════════════════════════════════════════════════════════${RESET}"
    echo -e "${GREEN}${BOLD}  ✅  Configuracao concluida!${RESET}"
    echo -e "${CYAN}${BOLD}  ══════════════════════════════════════════════════════════${RESET}"
    echo ""
    echo -e "  ${BOLD}O que esta ativo no seu ambiente:${RESET}"
    echo ""
    echo -e "  ${GREEN}▸${RESET}  ${BOLD}Hook commit-msg${RESET}"
    echo -e "      Todo ${CYAN}git commit${RESET} valida automaticamente a mensagem."
    echo -e "      Commits fora do padrao sao bloqueados antes de serem gravados."
    echo ""
    echo -e "  ${GREEN}▸${RESET}  ${BOLD}Template de commit (.gitmessage)${RESET}"
    echo -e "      Ao rodar ${CYAN}git commit${RESET} sem ${CYAN}-m${RESET}, o editor abre com o template."
    echo -e "      Complete a ultima linha e salve o arquivo."
    echo ""
    echo -e "  ${GREEN}▸${RESET}  ${BOLD}Workflows GitHub Actions${RESET}"
    echo -e "      A cada push, o GitHub valida mensagens e qualidade de codigo."
    echo -e "      Merge bloqueado automaticamente se qualquer check falhar."
    echo ""
    echo -e "  ${BOLD}Formato obrigatorio de commit:${RESET}"
    echo ""
    echo -e "    ${CYAN}[TICKET-NNN]-tipo-Descricao longa aqui${RESET}"
    echo ""
    echo -e "  ${BOLD}Exemplos:${RESET}"
    echo -e "    ${GREEN}git commit -m \"[DRB-001]-feat-New Class Sound Cars\"${RESET}"
    echo -e "    ${GREEN}git commit -m \"[ABC-042]-fix-Corrige bug no calculo de imposto\"${RESET}"
    echo -e "    ${GREEN}git commit -m \"[PROJ-99]-ci-Adiciona validacao no pipeline\"${RESET}"
    echo ""
    echo -e "  ${BOLD}Tipos aceitos:${RESET}"
    echo -e "    ${GREY}feat  fix  docs  style  refactor  perf  test${RESET}"
    echo -e "    ${GREY}build  ci  chore  revert  hotfix  release${RESET}"
    echo ""
    echo -e "  ${GREY}Duvidas? Consulte .github/workflows/_README.md${RESET}"
    echo ""
}

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

main() {
    print_banner
    check_prerequisites
    configure_hooks
    configure_commit_template
    validate_required_files
    print_summary
}

main "$@"
