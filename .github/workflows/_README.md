# 📋 Workflows & Quality Pipeline — Documentação

> Documentação completa de todos os workflows, hooks e ferramentas de qualidade deste repositório.  
> Mantido por: **Code Quality Guardian** · Versão: **2.0.0**

---

## Índice

- [Visão Geral](#visão-geral)
- [Arquitetura do Pipeline](#arquitetura-do-pipeline)
- [Estrutura de Arquivos](#estrutura-de-arquivos)
- [Workflows GitHub Actions](#workflows-github-actions)
  - [📝 commit-message-lint.yml](#-commit-message-lintyml)
  - [🔍 code-quality.yml](#-code-qualityyml)
- [Hook Git Local](#hook-git-local)
  - [commit-msg](#commit-msg)
- [Ferramentas de Validação](#ferramentas-de-validação)
  - [code_validator.py](#code_validatorpy)
  - [validator_logger.py](#validator_loggerpy)
  - [run_validator.sh](#run_validatorsh)
- [Instalação e Configuração](#instalação-e-configuração)
- [Regras de Qualidade de Código](#regras-de-qualidade-de-código)
- [Padrão de Mensagem de Commit](#padrão-de-mensagem-de-commit)
- [Branch Protection](#branch-protection)
- [Entendendo os Logs](#entendendo-os-logs)
- [Decisões de Arquitetura](#decisões-de-arquitetura)
- [Referências](#referências)

---

## Visão Geral

Este repositório adota um pipeline de qualidade em **duas camadas independentes**, cada uma com responsabilidade única e bem definida:

| Camada | Onde roda | Responsabilidade | Arquivo |
|--------|-----------|------------------|---------|
| **1 — Hook local** | Máquina do dev | Bloqueia commit com mensagem inválida | `.githooks/commit-msg` |
| **2a — GitHub Action** | Servidor GitHub | Valida padrão da mensagem de commit | `commit-message-lint.yml` |
| **2b — GitHub Action** | Servidor GitHub | Valida qualidade do código-fonte | `code-quality.yml` |

A separação em workflows distintos segue o **Princípio da Responsabilidade Única (SRP)**:  
cada arquivo tem exatamente um motivo para existir e um motivo para mudar.

---

## Arquitetura do Pipeline

```
  Developer
      │
      │  git commit -m "[DRB-001]-feat-Minha feature"
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│  CAMADA 1 — Hook Local (.githooks/commit-msg)           │
│                                                         │
│  ✔ Mensagem válida   →  commit gravado localmente       │
│  ✘ Mensagem inválida →  commit BLOQUEADO na máquina     │
│                         (sem chegar ao GitHub)          │
└──────────────────────────┬──────────────────────────────┘
                           │  git push
                           ▼
                    GitHub recebe o push
                           │
           ┌───────────────┴────────────────┐
           │                                │
           ▼                                ▼
┌──────────────────────┐       ┌────────────────────────┐
│  CAMADA 2a           │       │  CAMADA 2b             │
│  commit-message-     │       │  code-quality.yml      │
│  lint.yml            │       │                        │
│                      │       │  Valida o código-fonte │
│  Re-valida padrão    │       │  de cada arquivo       │
│  da mensagem no      │       │  alterado no commit    │
│  servidor            │       │  (10 regras, fail-fast)│
│                      │       │                        │
│  ✔ PASSED            │       │  ✔ PASSED              │
│  ✘ FAILED → bloqueia │       │  ✘ FAILED → bloqueia   │
└──────────────────────┘       └────────────────────────┘
           │                                │
           └───────────────┬────────────────┘
                           ▼
                  Ambos aprovados?
                  Merge liberado ✅
```

> Os dois workflows rodam **em paralelo**, reduzindo o tempo total de feedback.

---

## Estrutura de Arquivos

```
.
├── .github/
│   └── workflows/
│       ├── _README.md                  ← Este arquivo
│       ├── commit-message-lint.yml     ← Workflow: valida mensagem de commit
│       └── code-quality.yml            ← Workflow: valida qualidade do código
│
├── .githooks/
│   └── commit-msg                      ← Hook Git local (barreira preventiva)
│
├── tools/
│   └── validator/
│       ├── code_validator.py           ← Motor de validação (10 regras)
│       ├── validator_logger.py         ← Sistema de logging estruturado
│       └── run_validator.sh            ← Orquestrador shell com log completo
│
└── setup-hooks.sh                      ← Instalador dos hooks (1x por dev)
```

---

## Workflows GitHub Actions

### 📝 `commit-message-lint.yml`

**Propósito único:** Garantir que toda mensagem de commit siga o padrão semântico definido pelo time.

#### Quando é acionado

| Evento | Detalhe |
|--------|---------|
| `push` | Qualquer branch, a cada novo commit enviado |
| `pull_request` | Abertura, atualização ou sincronização de PR |

#### Comportamento de concorrência

Quando um novo push chega no mesmo branch/PR, a execução anterior é **cancelada automaticamente** para evitar desperdício de recursos de CI.

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

#### Permissões

| Permissão | Nível | Motivo |
|-----------|-------|--------|
| `contents` | `read` | Leitura do histórico Git para extrair mensagens de commit |
| `pull-requests` | `write` | Publicar comentário automático no PR com o resultado |

#### Steps detalhados

```
Step 1 — 📥 Checkout
  Realiza o checkout com fetch-depth: 0 (histórico completo).
  Necessário para acessar commits anteriores via git log.

Step 2 — 🔎 Identificar commits do evento
  Para push   : valida o commit do SHA atual.
  Para PR     : valida TODOS os commits entre a base e o HEAD do PR.
  Salva a lista de SHAs em /tmp/commits_to_validate.txt.

Step 3 — ✅ Validar mensagens de commit
  Lê cada SHA da lista e extrai a primeira linha da mensagem.
  Aplica a regex do padrão obrigatório.
  Ignora commits automáticos do Git (Merge, Revert, fixup!, squash!).
  Retorna exit 1 se qualquer mensagem for inválida.

Step 4 — 📊 Publicar sumário
  Sempre executa (if: always()).
  Escreve tabela de resultado na aba Summary da execução.

Step 5 — 💬 Comentar no PR
  Somente em eventos pull_request.
  Cria ou ATUALIZA (sem duplicar) um comentário no PR com o resultado.
```

#### O que aparece no PR

Quando a validação **falha**, o bot publica:

```
❌ Commit Message Lint — Mensagens de commit fora do padrão

2 commit(s) reprovado(s):
- `a1b2c3d` → `adiciona nova classe`
- `e4f5g6h` → `fix bug`

Formato correto:
  [TICKET-NNN]-tipo-Descricao longa aqui
```

Quando **passa**:

```
✅ Commit Message Lint — Mensagens de commit aprovadas

Todos os 3 commit(s) estão no padrão exigido.
```

---

### 🔍 `code-quality.yml`

**Propósito único:** Validar a qualidade do código-fonte de cada arquivo alterado no commit, aplicando 10 regras de Clean Code com comportamento fail-fast.

#### Quando é acionado

| Evento | Detalhe |
|--------|---------|
| `push` | Qualquer branch, a cada novo commit enviado |
| `pull_request` | Abertura, atualização ou sincronização de PR |

#### Linguagens suportadas

`.java` `.js` `.ts` `.cs` `.cpp` `.c` `.h` `.hpp` `.apex` `.cls` `.py` `.kt` `.swift`

#### Comportamento diff-aware

O workflow **não valida o repositório inteiro** — apenas os arquivos **adicionados ou modificados** no commit ou PR. Isso garante:

- Feedback rápido e focado
- Sem penalizar código legado não relacionado à mudança
- Tempo de CI proporcional ao tamanho da alteração

```
Push direto  →  diff entre commit anterior e o atual
Pull Request →  diff entre a base do PR e o HEAD
```

#### Steps detalhados

```
Step 1 — 📥 Checkout
  fetch-depth: 0 para permitir git diff entre commits.

Step 2 — 🐍 Configurar Python 3.11
  Sem cache: "pip" — o validador usa apenas stdlib do Python.
  Não há requirements.txt nem pyproject.toml neste projeto.

Step 3 — 📦 Verificar dependências
  Valida que todos os módulos stdlib necessários estão disponíveis.
  Falha explicitamente antes de tentar validar se algo estiver errado.

Step 4 — 🔧 Preparar scripts do validador
  Garante permissão de execução no run_validator.sh.
  Testa a importação do validator_logger.py.

Step 5 — 🔎 Detectar arquivos alterados
  Executa git diff --name-only --diff-filter=ACMR
  (A=Added, C=Copied, M=Modified, R=Renamed — exclui deletados).
  Filtra por extensões suportadas.
  Exporta has_files=true|false para os steps seguintes.

Step 6 — 🔍 Executar validação de qualidade
  Itera sobre cada arquivo alterado.
  Executa code_validator.py para cada um.
  Comportamento fail-fast: para na primeira regra com violação.
  Retorna exit 1 se qualquer arquivo reprovar.

Step 7 — ⏭️ Nenhum arquivo de código alterado
  Executado quando has_files=false.
  Informa que a validação foi ignorada (commit só de docs, configs etc.).

Step 8 — 📤 Upload dos logs
  Sempre executa (if: always()), mesmo com falha.
  Publica 3 tipos de log como artefato retido por 30 dias:
    - validator_*.log  (texto legível)
    - validator_*.json (estruturado para ferramentas)
    - shell_*.log      (log do orquestrador)

Step 9 — 📊 Publicar sumário
  Sempre executa.
  Escreve tabela com commit, branch, autor e lista de regras.

Step 10 — 💬 Comentar no PR
  Somente em pull_request.
  Cria ou atualiza comentário com resultado e link para os logs.
```

#### Variáveis de ambiente usadas

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `VALIDATOR_AUTHOR` | `github.actor` | Nome do executor nos logs |
| `VALIDATOR_LOG_KEEP` | `20` | Máximo de logs retidos por tipo |
| `NO_COLOR` | `1` | Desativa cores ANSI nos logs do Actions |

#### Artefatos gerados

Após cada execução, os logs ficam disponíveis na aba **Actions → Artifacts**:

```
validator-logs-{run_number}-{sha}/
├── validator_YYYYMMDD_HHMMSS.log    ← Texto legível por humanos
├── validator_YYYYMMDD_HHMMSS.json   ← Estruturado (CI/CD, dashboards)
└── shell_YYYYMMDD_HHMMSS.log        ← Log do orquestrador shell
```

Retidos por **30 dias**.

---

## Hook Git Local

### `commit-msg`

**Localização:** `.githooks/commit-msg`  
**Propósito:** Ser a **primeira barreira** de validação — bloquear o commit na máquina do desenvolvedor antes que ele chegue ao GitHub, dando feedback imediato sem consumir CI.

#### Como funciona

O Git executa este script automaticamente durante `git commit`, passando o arquivo com a mensagem como argumento `$1`. O script lê o arquivo, aplica a mesma regex do workflow remoto e retorna:

- `exit 0` → commit permitido
- `exit 1` → commit bloqueado, mensagem de erro exibida no terminal

#### Commits automáticos ignorados

O hook **não bloqueia** commits gerados pelo próprio Git:

| Prefixo ignorado | Situação |
|-----------------|----------|
| `Merge branch` | Merge local entre branches |
| `Merge pull request` | Merge vindo do GitHub |
| `Merge remote` | Merge com remote tracking branch |
| `Revert ` | Revert gerado pelo `git revert` |
| `fixup!` | Commit de fixup para rebase interativo |
| `squash!` | Commit de squash para rebase interativo |

#### Mensagem de erro no terminal

Quando o commit é bloqueado, o desenvolvedor vê:

```
  ╔══════════════════════════════════════════════════════════════╗
  ║   ❌  COMMIT BLOQUEADO — Mensagem fora do padrão            ║
  ╚══════════════════════════════════════════════════════════════╝

  Mensagem recebida:
    → "feat adiciona nova classe"

  Formato obrigatório:
    [TICKET-NNN]-tipo-Descricao com pelo menos tres palavras

  Exemplos válidos:
    ✔  [DRB-001]-feat-New Class Sound Cars
    ✔  [ABC-042]-fix-Corrige bug no calculo de imposto

  Dica: edite sua mensagem com:
    git commit --amend -m "[DRB-001]-feat-Sua descricao aqui"
```

---

## Ferramentas de Validação

### `code_validator.py`

**Motor principal** do sistema de qualidade. Implementa as 10 regras de validação usando os padrões **Strategy**, **Composite**, **Builder** e **Facade**.

#### Arquitetura interna

```
CodeValidator (Facade)
    └── RuleSet (Composite — Chain of Responsibility com fail-fast)
            ├── ExcessiveParametersRule   (R01 — Strategy)
            ├── MissingNullCheckRule      (R02 — Strategy)
            ├── QueryOutsideDaoRule       (R03 — Strategy)
            ├── MagicNumberRule           (R04 — Strategy)
            ├── MagicStringRule           (R05 — Strategy)
            ├── LongVariableNameRule      (R06 — Strategy)
            ├── ShortVariableNameRule     (R07 — Strategy)
            ├── NestedForRule             (R08 — Strategy)
            ├── NestedIfRule              (R09 — Strategy)
            └── QueryInsideLoopRule       (R10 — Strategy)
```

#### Comportamento fail-fast

```
R01 executa → 0 violações → R02 executa → 0 violações → R03 executa ...
                                                              │
                                                    3 violações encontradas
                                                              │
                                              Pipeline CANCELADO imediatamente
                                              R04 ... R10 → marcadas como SKIPPED
```

#### SourceSanitizer

Antes de cada análise, o código passa pelo `SourceSanitizer` que remove comentários e strings literais. Isso evita **falsos positivos** como:

- Um número dentro de um comentário sendo acusado de "número mágico"
- Uma string dentro de um comentário sendo acusada de "string mágica"
- Uma query dentro de um comentário de Javadoc sendo detectada como query real

---

### `validator_logger.py`

**Sistema de logging** com padrão **Singleton** e **Decorator**. Produz dois formatos de saída simultaneamente.

#### Saídas geradas

**Arquivo `.log` (texto):**
```
[2024-01-15 10:32:01] [INFO   ]  ▶  [R01] Excesso de parâmetros — iniciando...
[2024-01-15 10:32:01] [INFO   ]  ■  [R01] Excesso de parâmetros | PASSED | 0 violação(ões) | 1.24 ms
[2024-01-15 10:32:01] [INFO   ]  ▶  [R02] Parâmetro sem null check — iniciando...
[2024-01-15 10:32:01] [WARNING]  ■  [R02] Parâmetro sem null check | FAILED | 2 violação(ões) | 0.87 ms  ← PIPELINE CANCELADO
```

**Arquivo `.json` (estruturado):**
```json
{
  "session_id": "uuid-aqui",
  "tool_name": "Universal Code Validator",
  "tool_version": "2.0.0",
  "author": "github-actor",
  "started_at": "2024-01-15T10:32:00Z",
  "finished_at": "2024-01-15T10:32:02Z",
  "total_duration_ms": 1842.3,
  "target_path": "src/MinhaClasse.java",
  "files_analyzed": 1,
  "total_violations": 2,
  "overall_status": "ABORTED",
  "aborted_at_rule": "R02",
  "rules": [
    {
      "rule_id": "R01",
      "rule_name": "Excesso de parâmetros (> 3)",
      "status": "PASSED",
      "duration_ms": 1.24,
      "violations": 0,
      "aborted_chain": false
    },
    {
      "rule_id": "R02",
      "rule_name": "Parâmetro sem validação de null",
      "status": "FAILED",
      "duration_ms": 0.87,
      "violations": 2,
      "aborted_chain": true
    }
  ]
}
```

#### Status possíveis por sessão

| Status | Significado |
|--------|-------------|
| `PASSED` | Todas as regras executaram sem violações |
| `FAILED` | Alguma regra encontrou violações (todas rodaram) |
| `ABORTED` | Pipeline interrompido na primeira falha (fail-fast) |

#### Status possíveis por regra

| Status | Significado |
|--------|-------------|
| `PASSED` | Regra executou sem encontrar violações |
| `FAILED` | Regra encontrou uma ou mais violações |
| `SKIPPED` | Regra não executou pois pipeline foi cancelado antes |
| `ERROR` | Exceção inesperada durante a execução da regra |

---

### `run_validator.sh`

**Orquestrador shell** responsável por verificar pré-requisitos, executar o validador Python, exibir os logs e realizar rotação de arquivos de log.

#### Fluxo de execução

```
1. Verifica Python (versão mínima 3.8)
2. Verifica existência dos scripts Python
3. Verifica módulos stdlib disponíveis
4. Rotaciona logs antigos (retém os N mais recentes)
5. Executa code_validator.py
6. Exibe o log texto gerado
7. Exibe tabela resumo do JSON
8. Retorna exit code (0 = sucesso, 1 = falha)
```

#### Variáveis de ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `VALIDATOR_AUTHOR` | `$USER` | Nome exibido no cabeçalho do log |
| `VALIDATOR_LOG_KEEP` | `10` | Quantidade de logs retidos por tipo |
| `VALIDATOR_PYTHON` | `python3` | Caminho do executável Python |
| `NO_COLOR` | não definida | Se definida, desativa cores ANSI |

#### Uso direto

```bash
# Arquivo único
./tools/validator/run_validator.sh MinhaClasse.java

# Diretório inteiro
./tools/validator/run_validator.sh ./src

# Com extensões específicas
./tools/validator/run_validator.sh ./src .java .apex

# Com autor personalizado
VALIDATOR_AUTHOR="João Silva" ./tools/validator/run_validator.sh ./src

# Sem cores (útil para pipelines)
NO_COLOR=1 ./tools/validator/run_validator.sh ./src
```

---

## Instalação e Configuração

### Pré-requisitos

- Git 2.9+
- Python 3.8+
- Acesso de escrita ao repositório (para configurar Branch Protection)

### Passo 1 — Clonar e instalar hooks

```bash
# Clone o repositório
git clone https://github.com/org/seu-repositorio.git
cd seu-repositorio

# Instale os hooks locais (execute UMA vez)
./setup-hooks.sh
```

O script `setup-hooks.sh` faz exatamente três coisas:
1. `git config core.hooksPath .githooks` — aponta o Git para os hooks do projeto
2. `chmod +x .githooks/*` — garante permissão de execução
3. Exibe confirmação de instalação

### Passo 2 — Verificar instalação

```bash
# Tente um commit com mensagem inválida — deve ser bloqueado
git commit --allow-empty -m "mensagem invalida"

# Deve aparecer o erro com instruções

# Agora com mensagem válida — deve passar
git commit --allow-empty -m "[DRB-001]-test-Verificando instalacao do hook"
```

### Passo 3 — Copiar arquivos para o repositório

Certifique-se de que estes arquivos estão commitados:

```
.github/workflows/commit-message-lint.yml
.github/workflows/code-quality.yml
.github/workflows/_README.md
.githooks/commit-msg
tools/validator/code_validator.py
tools/validator/validator_logger.py
tools/validator/run_validator.sh
setup-hooks.sh
```

### Passo 4 — Configurar Branch Protection no GitHub

Acesse: `Settings → Branches → Add branch protection rule`

| Campo | Valor |
|-------|-------|
| Branch name pattern | `main` (ou `master`, conforme o projeto) |
| Require status checks to pass | ✅ ativado |
| Status checks obrigatórios | `Lint — Commit Messages` e `Validate` |
| Require branches to be up to date | ✅ ativado |
| Do not allow bypassing the above settings | ✅ recomendado |

> Após configurar, **nenhum merge** será permitido enquanto qualquer um dos dois checks estiver falhando.

---

## Regras de Qualidade de Código

Todas as regras seguem princípios do livro **Clean Code** de Robert C. Martin e **Programação Defensiva**.

| ID | Nome | Severidade | Mensagem | Referência |
|----|------|-----------|---------|------------|
| **R01** | Excesso de parâmetros | ⚠️ WARNING | `O método X possui N parâmetros. Mais de 3 — é necessário refatorar.` | Clean Code, Cap. 3 |
| **R02** | Parâmetro sem validação de null | ⚠️ WARNING | `O parâmetro X do método Y não tem validação de null/blank/empty.` | Defensive Programming |
| **R03** | Query fora de classe DAO | ⚠️ WARNING | `Query existe no método X. Por favor, mova-a para uma classe DAO.` | Separation of Concerns |
| **R04** | Número mágico | ⚠️ WARNING | `Número mágico 42! Coloque em uma variável.` | Clean Code, Cap. 17 |
| **R05** | String mágica | ⚠️ WARNING | `String mágica! Passe "texto" para uma variável.` | Clean Code, Cap. 17 |
| **R06** | Nome de variável muito longo | ⚠️ WARNING | `A variável X está muito grande (N chars). Reduza!` | Clean Code, Cap. 2 |
| **R07** | Nome de variável muito curto | ⚠️ WARNING | `Variável X está muito curta! Use nomes mais descritivos.` | Clean Code, Cap. 2 |
| **R08** | For encadeado (≥ 3 níveis) | ❌ ERROR | `For encadeado! Refaça sua lógica! ❌` | Clean Code, Cap. 3 |
| **R09** | If encadeado (≥ 3 níveis) | ⚠️ WARNING | `Ifs encadeados! Refaça sua lógica.` | Clean Code, Cap. 3 |
| **R10** | Query dentro de laço | ❌ ERROR | `Query dentro de Laço! Remova a query e refaça sua lógica.` | Performance / Clean Code |

### Observações importantes sobre as regras

**R01 — Excesso de parâmetros**  
Mais de 3 parâmetros indica que o método está fazendo mais de uma coisa. A solução típica é criar um objeto de parâmetros (Parameter Object) ou dividir o método.

**R02 — Validação de null**  
O validador inspeciona o corpo do método em busca de qualquer uma das seguintes verificações: `!= null`, `== null`, `isBlank()`, `isEmpty()`, `Objects.requireNonNull()`, `StringUtils.isEmpty()`, `is not None`. A regra **não se aplica** a tipos primitivos.

**R03 — Query fora de DAO**  
A regra é **automaticamente ignorada** se a classe contiver as palavras `DAO`, `Dao`, `Repository`, `Repo`, `Mapper`, `Gateway` ou `Persistence` no nome. Suporta SQL padrão, SOQL (Apex) e métodos ORM comuns.

**R06 / R07 — Tamanho de variáveis**  
Variáveis de loop convencionais (`i`, `j`, `k`) e abreviações amplamente aceitas (`id`, `db`, `err`, `ok`) são **isentas** da regra R07.

**R08 / R09 — Aninhamento**  
A contagem de níveis é feita rastreando a profundidade de chaves `{}`. Comentários e strings são removidos antes da análise para evitar falsos positivos.

---

## Padrão de Mensagem de Commit

### Formato

```
[TICKET-NNN]-tipo-Descrição com pelo menos 10 caracteres
```

### Componentes

| Componente | Regra | Exemplos válidos | Exemplos inválidos |
|-----------|-------|------------------|--------------------|
| `[TICKET-NNN]` | Letras **MAIÚSCULAS**, hífen, número | `[DRB-001]` `[ABC-42]` `[PROJ-999]` | `[drb-001]` `[DRB001]` `DRB-001` |
| `-tipo-` | Tipo semântico em **minúsculas** da lista | `-feat-` `-fix-` `-ci-` | `-FEAT-` `-feature-` `-bugfix-` |
| `Descrição` | Texto livre, mínimo **10 caracteres** | `New Class Sound Cars` | `Fix` `Update` |

### Tipos semânticos aceitos

| Tipo | Quando usar |
|------|-------------|
| `feat` | Nova funcionalidade para o usuário |
| `fix` | Correção de bug |
| `docs` | Alterações apenas em documentação |
| `style` | Formatação, ponto e vírgula, sem mudança de lógica |
| `refactor` | Refatoração de código sem nova feature nem bugfix |
| `perf` | Melhoria de performance |
| `test` | Adição ou correção de testes |
| `build` | Mudanças no sistema de build ou dependências externas |
| `ci` | Mudanças em arquivos de CI/CD |
| `chore` | Tarefas de manutenção sem mudança em produção |
| `revert` | Reversão de commit anterior |
| `hotfix` | Correção crítica e urgente em produção |
| `release` | Preparação de release |

### Exemplos completos

```bash
# ✅ Válidos
git commit -m "[DRB-001]-feat-New Class Sound Cars"
git commit -m "[ABC-042]-fix-Corrige bug no calculo de imposto"
git commit -m "[PROJ-99]-refactor-Reorganiza estrutura de pastas do core"
git commit -m "[DRB-007]-ci-Adiciona validacao de qualidade no pipeline"
git commit -m "[DRB-010]-docs-Atualiza README com instrucoes de instalacao"
git commit -m "[ABC-100]-test-Adiciona testes unitarios para CarService"

# ❌ Inválidos
git commit -m "feat: adiciona classe"               # sem ticket
git commit -m "[DRB-001] feat nova classe"          # sem hifens separadores
git commit -m "[drb-001]-feat-Descricao"            # ticket com minúsculas
git commit -m "[DRB-001]-unknown-Descricao longa"   # tipo inválido
git commit -m "[DRB-001]-feat-Curto"                # descrição com menos de 10 chars
```

### Commits ignorados (sem validação)

Os seguintes prefixos são gerados automaticamente pelo Git e **não são validados**:

- `Merge branch ...`
- `Merge pull request ...`
- `Merge remote ...`
- `Revert "..."`
- `fixup! ...`
- `squash! ...`

---

## Branch Protection

Para que o pipeline funcione como **porta de entrada obrigatória** antes de qualquer merge, configure as regras de proteção no GitHub:

### Configuração recomendada para `main`

```
Settings → Branches → Branch protection rules → Add rule

Branch name pattern: main

✅ Require a pull request before merging
   ✅ Require approvals: 1 (ou mais, conforme o time)
   ✅ Dismiss stale pull request approvals when new commits are pushed

✅ Require status checks to pass before merging
   ✅ Require branches to be up to date before merging
   Status checks obrigatórios:
     → Lint — Commit Messages
     → Validate

✅ Require conversation resolution before merging

✅ Do not allow bypassing the above settings
```

### Status checks que aparecem no PR

| Check | Workflow | Passa quando |
|-------|----------|-------------|
| `Lint — Commit Messages` | `commit-message-lint.yml` | Todos os commits do PR seguem o padrão |
| `Validate` | `code-quality.yml` | Todos os arquivos alterados passam nas 10 regras |

---

## Entendendo os Logs

### Como acessar os logs de uma execução

1. Acesse a aba **Actions** do repositório
2. Clique na execução desejada
3. No job `validate` ou `lint-commit-messages`, clique em qualquer step para ver o output
4. Role até o final para encontrar o link dos **Artifacts**
5. Baixe o `.zip` com os três arquivos de log

### Interpretando o log texto (`.log`)

```
[2024-01-15 10:32:00] [INFO   ]  SESSÃO INICIADA  | id=abc-123
[2024-01-15 10:32:00] [INFO   ]  Ferramenta       : Universal Code Validator v2.0.0
[2024-01-15 10:32:00] [INFO   ]  Autor            : github-actor
[2024-01-15 10:32:00] [INFO   ]  Host             : runner-abc
[2024-01-15 10:32:00] [INFO   ]  SO               : Linux 5.15.0
[2024-01-15 10:32:00] [INFO   ]  Alvo             : src/MinhaClasse.java
─────────────────────────────────────────────────
[2024-01-15 10:32:01] [INFO   ]  ▶  [R01] Excesso de parâmetros — iniciando...
[2024-01-15 10:32:01] [INFO   ]  ■  [R01] PASSED | 0 violação(ões) | 1.24 ms
[2024-01-15 10:32:01] [INFO   ]  ▶  [R02] Parâmetro sem null check — iniciando...
[2024-01-15 10:32:01] [WARNING]  ■  [R02] FAILED | 2 violação(ões) | 0.87 ms  ← PIPELINE CANCELADO
[2024-01-15 10:32:01] [INFO   ]  [R03] SKIPPED — Pipeline cancelado pela regra R02
...
[2024-01-15 10:32:01] [INFO   ]  SESSÃO ENCERRADA | status=ABORTED
[2024-01-15 10:32:01] [INFO   ]  Arquivos analisados : 1
[2024-01-15 10:32:01] [INFO   ]  Total de violações  : 2
[2024-01-15 10:32:01] [INFO   ]  Duração total       : 42.15 ms
[2024-01-15 10:32:01] [WARNING]  ABORTADO na regra   : R02
```

### Consumindo o log JSON em ferramentas externas

O arquivo `.json` pode ser integrado a dashboards, Slack bots ou relatórios de qualidade:

```bash
# Exemplo: extrair status geral com jq
cat validator_*.json | jq '.overall_status'

# Listar regras que falharam
cat validator_*.json | jq '.rules[] | select(.status == "FAILED")'

# Ver tempo total de execução
cat validator_*.json | jq '.total_duration_ms'
```

---

## Decisões de Arquitetura

### Por que dois workflows separados e não um único?

Seguindo o **Princípio da Responsabilidade Única (SRP)** aplicado a workflows:

- `commit-message-lint.yml` tem exatamente **um motivo para mudar**: a política de nomenclatura de commits
- `code-quality.yml` tem exatamente **um motivo para mudar**: as regras de qualidade de código

Se fossem um único arquivo, uma mudança na regex do commit poderia acidentalmente quebrar a validação de código, e vice-versa. Separados, cada workflow pode **evoluir independentemente**.

### Por que um hook local além do workflow remoto?

O hook local é a **barreira preventiva** — dá feedback instantâneo ao desenvolvedor sem precisar consumir minutos de CI. O workflow remoto é a **barreira garantidora** — protege o repositório mesmo que o dev não tenha instalado o hook (novo membro do time, clone em máquina diferente, etc.).

### Por que fail-fast nas regras de código?

Ao parar na primeira regra com violação, o desenvolvedor recebe um feedback **focado e acionável**: corrija esta regra específica. Se todas as regras rodassem, uma lista com 30 violações de 8 regras diferentes seria cognitivamente mais difícil de processar e corrigir.

### Por que apenas stdlib Python (sem dependências externas)?

Zero dependências externas significa:
- Sem `pip install` no CI (mais rápido)
- Sem problemas de versão de pacotes
- Sem vulnerabilidades de supply chain
- Funciona em qualquer ambiente com Python 3.8+

---

## Referências

- [Clean Code — Robert C. Martin](https://www.amazon.com.br/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [Defensive Programming — Wikipedia](https://en.wikipedia.org/wiki/Defensive_programming)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Actions — Documentação oficial](https://docs.github.com/en/actions)
- [Git Hooks — Documentação oficial](https://git-scm.com/docs/githooks)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

---

> **Mantenedor:** Code Quality Guardian  
> **Última atualização:** 2024  
> **Versão do pipeline:** 2.0.0
