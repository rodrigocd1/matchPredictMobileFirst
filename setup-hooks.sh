#!/usr/bin/env bash
# =============================================================================
#  setup-hooks.sh
#
#  Instala os Git hooks do projeto localmente.
#  Execute UMA vez apos clonar o repositorio.
#
#  Uso:
#    ./setup-hooks.sh
#
#  O que faz:
#    1. Aponta o Git para a pasta .githooks/ deste repositorio
#    2. Garante que os hooks tenham permissao de execucao
#    3. Testa se o hook esta funcionando
#
#  Autor   : Code Quality Guardian
#  Versao  : 1.0.0
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="${SCRIPT_DIR}/.githooks"

# Cores
if [ -t 1 ]; then
    GREEN='\033[0;92m'; YELLOW='\033[0;93m'; RED='\033[0;91m'
    CYAN='\033[0;96m';  BOLD='\033[1m';      RESET='\033[0m'
else
    GREEN=''; YELLOW=''; RED=''; CYAN=''; BOLD=''; RESET=''
fi

echo ""
echo -e "${CYAN}${BOLD}  Instalando Git Hooks — Commit Message Validator${RESET}"
echo -e "${CYAN}  ═══════════════════════════════════════════════${RESET}"
echo ""

# Verifica se esta dentro de um repositorio Git
if ! git -C "${SCRIPT_DIR}" rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}  ✘  Nao e um repositorio Git: ${SCRIPT_DIR}${RESET}"
    exit 1
fi

# Verifica se a pasta .githooks existe
if [ ! -d "${HOOKS_DIR}" ]; then
    echo -e "${RED}  ✘  Pasta .githooks nao encontrada em: ${HOOKS_DIR}${RESET}"
    exit 1
fi

# Garante permissao de execucao em todos os hooks
echo -e "  Aplicando permissoes de execucao em .githooks/..."
chmod +x "${HOOKS_DIR}"/*
echo -e "${GREEN}  ✔  Permissoes aplicadas.${RESET}"

# Configura o Git para usar a pasta .githooks deste projeto
echo -e "  Configurando core.hooksPath..."
git -C "${SCRIPT_DIR}" config core.hooksPath .githooks
echo -e "${GREEN}  ✔  core.hooksPath = .githooks${RESET}"

# Verifica se o hook commit-msg existe
if [ -f "${HOOKS_DIR}/commit-msg" ]; then
    echo -e "${GREEN}  ✔  Hook commit-msg encontrado.${RESET}"
else
    echo -e "${YELLOW}  ⚠  Hook commit-msg nao encontrado em .githooks/${RESET}"
fi

echo ""
echo -e "${GREEN}${BOLD}  Instalacao concluida! ✅${RESET}"
echo ""
echo -e "  A partir de agora, todo ${BOLD}git commit${RESET} sera validado automaticamente."
echo -e "  Formato exigido: ${CYAN}[TICKET-NNN]-tipo-Descricao longa aqui${RESET}"
echo ""
echo -e "  Exemplo:"
echo -e "    ${GREEN}git commit -m \"[DRB-001]-feat-New Class Sound Cars\"${RESET}"
echo ""
