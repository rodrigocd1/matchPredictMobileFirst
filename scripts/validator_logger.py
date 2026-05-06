"""
validator_logger.py
===================
Sistema de logging estruturado para o Universal Code Validator.

Responsabilidades:
  - Registrar cada regra executada (início, fim, resultado)
  - Persistir log em arquivo .log (texto legível) e .json (estruturado)
  - Incluir metadados completos: autor, versão, datas, duração, host, SO
  - Suportar níveis: DEBUG | INFO | WARNING | ERROR | CRITICAL

Padrões aplicados:
  - Singleton  : garante uma única instância do logger por execução
  - Decorator  : `log_rule` cronometra e registra qualquer regra automaticamente
  - Observer   : handlers plugáveis (console, arquivo texto, arquivo JSON)

Autor   : Code Quality Guardian
Versão  : 2.0.0
"""

from __future__ import annotations

import json
import logging
import os
import platform
import socket
import sys
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

# ---------------------------------------------------------------------------
# Constantes de metadados da ferramenta
# ---------------------------------------------------------------------------

TOOL_NAME    = "Universal Code Validator"
TOOL_VERSION = "2.0.0"
TOOL_AUTHOR  = "Code Quality Guardian"
TOOL_REPO    = "https://github.com/org/universal-code-validator"

LOG_DIR      = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

_SESSION_TS  = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
LOG_FILE_TXT = LOG_DIR / f"validator_{_SESSION_TS}.log"
LOG_FILE_JSON= LOG_DIR / f"validator_{_SESSION_TS}.json"


# ---------------------------------------------------------------------------
# Value Objects para estrutura do log
# ---------------------------------------------------------------------------

class RuleStatus(str, Enum):
    PASSED  = "PASSED"
    FAILED  = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR   = "ERROR"


@dataclass
class RuleLogEntry:
    rule_id       : str
    rule_name     : str
    status        : RuleStatus
    started_at    : str
    finished_at   : str
    duration_ms   : float
    violations    : int        = 0
    aborted_chain : bool       = False
    error_detail  : str        = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class SessionLog:
    session_id       : str
    tool_name        : str          = TOOL_NAME
    tool_version     : str          = TOOL_VERSION
    author           : str          = TOOL_AUTHOR
    repository       : str          = TOOL_REPO
    python_version   : str          = field(default_factory=lambda: sys.version.split()[0])
    host             : str          = field(default_factory=socket.gethostname)
    operating_system : str          = field(default_factory=lambda: f"{platform.system()} {platform.release()}")
    user             : str          = field(default_factory=lambda: os.environ.get("USER", os.environ.get("USERNAME", "unknown")))
    started_at       : str          = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at      : str          = ""
    total_duration_ms: float        = 0.0
    target_path      : str          = ""
    files_analyzed   : int          = 0
    total_violations : int          = 0
    aborted_at_rule  : str          = ""
    overall_status   : str          = "RUNNING"
    rules            : list[dict]   = field(default_factory=list)
    summary_messages : list[str]    = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Singleton Logger
# ---------------------------------------------------------------------------

class ValidatorLogger:
    """
    Logger singleton. Escreve simultaneamente em:
      1. Console (stdout) com cores ANSI
      2. Arquivo .log  (texto legível por humanos)
      3. Arquivo .json (estruturado, consumível por ferramentas CI/CD)
    """

    _instance: Optional["ValidatorLogger"] = None

    # ANSI color codes
    _COLORS = {
        "RESET"   : "\033[0m",
        "BOLD"    : "\033[1m",
        "GREEN"   : "\033[92m",
        "YELLOW"  : "\033[93m",
        "RED"     : "\033[91m",
        "CYAN"    : "\033[96m",
        "MAGENTA" : "\033[95m",
        "WHITE"   : "\033[97m",
        "GREY"    : "\033[90m",
    }

    def __new__(cls) -> "ValidatorLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized  = True
        self._session      : Optional[SessionLog] = None
        self._session_start: float = 0.0
        self._use_color    : bool  = sys.stdout.isatty()

        # Python stdlib logger (arquivo texto)
        self._file_logger = logging.getLogger("validator")
        self._file_logger.setLevel(logging.DEBUG)

        fmt = logging.Formatter(
            fmt     = "[%(asctime)s] [%(levelname)-8s] %(message)s",
            datefmt = "%Y-%m-%d %H:%M:%S",
        )
        fh = logging.FileHandler(LOG_FILE_TXT, encoding="utf-8")
        fh.setFormatter(fmt)
        self._file_logger.addHandler(fh)

        # JSON log acumulado em memória → persiste ao finalizar sessão
        self._json_entries: list[dict] = []

    # ── Sessão ─────────────────────────────────────────────────────────────

    def begin_session(self, target_path: str) -> None:
        import uuid
        self._session_start = time.perf_counter()
        self._session = SessionLog(
            session_id  = str(uuid.uuid4()),
            started_at  = datetime.now(timezone.utc).isoformat(),
            target_path = target_path,
        )
        self._write_header()
        self._file_logger.info("=" * 70)
        self._file_logger.info(f"SESSÃO INICIADA  | id={self._session.session_id}")
        self._file_logger.info(f"Ferramenta       : {TOOL_NAME} v{TOOL_VERSION}")
        self._file_logger.info(f"Autor            : {TOOL_AUTHOR}")
        self._file_logger.info(f"Repositório      : {TOOL_REPO}")
        self._file_logger.info(f"Python           : {self._session.python_version}")
        self._file_logger.info(f"Host             : {self._session.host}")
        self._file_logger.info(f"SO               : {self._session.operating_system}")
        self._file_logger.info(f"Usuário          : {self._session.user}")
        self._file_logger.info(f"Alvo             : {target_path}")
        self._file_logger.info("=" * 70)

    def end_session(
        self,
        files_analyzed   : int,
        total_violations : int,
        aborted_at_rule  : str = "",
    ) -> None:
        if self._session is None:
            return

        elapsed = (time.perf_counter() - self._session_start) * 1000
        self._session.finished_at       = datetime.now(timezone.utc).isoformat()
        self._session.total_duration_ms = round(elapsed, 2)
        self._session.files_analyzed    = files_analyzed
        self._session.total_violations  = total_violations
        self._session.aborted_at_rule   = aborted_at_rule
        self._session.overall_status    = "ABORTED" if aborted_at_rule else (
            "FAILED" if total_violations > 0 else "PASSED"
        )

        status_label = {
            "PASSED"  : f"{self._c('GREEN')}✅  PASSED{self._c('RESET')}",
            "FAILED"  : f"{self._c('YELLOW')}⚠️  FAILED{self._c('RESET')}",
            "ABORTED" : f"{self._c('RED')}🛑  ABORTED{self._c('RESET')}",
        }.get(self._session.overall_status, self._session.overall_status)

        self._file_logger.info("=" * 70)
        self._file_logger.info(f"SESSÃO ENCERRADA | status={self._session.overall_status}")
        self._file_logger.info(f"Arquivos analisados : {files_analyzed}")
        self._file_logger.info(f"Total de violações  : {total_violations}")
        self._file_logger.info(f"Duração total       : {elapsed:.2f} ms")
        if aborted_at_rule:
            self._file_logger.warning(f"ABORTADO na regra   : {aborted_at_rule}")
        self._file_logger.info("=" * 70)

        self._print(f"\n{'═'*70}")
        self._print(f"  Status final  : {status_label}")
        self._print(f"  Arquivos      : {files_analyzed}")
        self._print(f"  Violações     : {total_violations}")
        self._print(f"  Duração       : {elapsed:.2f} ms")
        if aborted_at_rule:
            self._print(f"  {self._c('RED')}🛑 Abortado na regra {aborted_at_rule}{self._c('RESET')}")
        self._print(f"  Log texto     : {LOG_FILE_TXT}")
        self._print(f"  Log JSON      : {LOG_FILE_JSON}")
        self._print(f"{'═'*70}\n")

        # Persiste JSON
        self._session.rules = self._json_entries
        LOG_FILE_JSON.write_text(
            json.dumps(self._session.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── Regras ─────────────────────────────────────────────────────────────

    def log_rule_start(self, rule_id: str, rule_name: str) -> float:
        """Registra início de uma regra e retorna o timestamp de início."""
        start = time.perf_counter()
        msg = f"▶  [{rule_id}] {rule_name} — iniciando..."
        self._file_logger.info(msg)
        self._print(f"  {self._c('CYAN')}▶{self._c('RESET')}  [{self._c('BOLD')}{rule_id}{self._c('RESET')}] {rule_name}")
        return start

    def log_rule_end(
        self,
        rule_id     : str,
        rule_name   : str,
        start_ts    : float,
        violations  : int,
        aborted     : bool = False,
        error       : str  = "",
    ) -> RuleLogEntry:
        elapsed = (time.perf_counter() - start_ts) * 1000

        if error:
            status = RuleStatus.ERROR
        elif aborted:
            status = RuleStatus.FAILED
        elif violations > 0:
            status = RuleStatus.FAILED
        else:
            status = RuleStatus.PASSED

        entry = RuleLogEntry(
            rule_id       = rule_id,
            rule_name     = rule_name,
            status        = status,
            started_at    = datetime.now(timezone.utc).isoformat(),
            finished_at   = datetime.now(timezone.utc).isoformat(),
            duration_ms   = round(elapsed, 2),
            violations    = violations,
            aborted_chain = aborted,
            error_detail  = error,
        )
        self._json_entries.append(entry.to_dict())

        icon, color = {
            RuleStatus.PASSED  : ("✅", "GREEN"),
            RuleStatus.FAILED  : ("❌", "YELLOW"),
            RuleStatus.ERROR   : ("💥", "RED"),
            RuleStatus.SKIPPED : ("⏭️", "GREY"),
        }[status]

        msg_console = (
            f"  {icon}  [{rule_id}] {rule_name} "
            f"| {self._c(color)}{status.value}{self._c('RESET')} "
            f"| {violations} violação(ões) "
            f"| {elapsed:.2f} ms"
        )
        msg_file = (
            f"■  [{rule_id}] {rule_name} | {status.value} "
            f"| {violations} violação(ões) | {elapsed:.2f} ms"
        )

        if aborted:
            msg_console += f"  {self._c('RED')}← PIPELINE CANCELADO{self._c('RESET')}"
            msg_file    += "  ← PIPELINE CANCELADO"

        self._print(msg_console)
        log_fn = (
            self._file_logger.error   if status == RuleStatus.ERROR   else
            self._file_logger.warning if status == RuleStatus.FAILED  else
            self._file_logger.info
        )
        log_fn(msg_file)
        if error:
            self._file_logger.error(f"   Detalhe do erro: {error}")

        return entry

    def log_rule_skipped(self, rule_id: str, rule_name: str, reason: str) -> None:
        self._json_entries.append(RuleLogEntry(
            rule_id     = rule_id,
            rule_name   = rule_name,
            status      = RuleStatus.SKIPPED,
            started_at  = datetime.now(timezone.utc).isoformat(),
            finished_at = datetime.now(timezone.utc).isoformat(),
            duration_ms = 0.0,
            error_detail= reason,
        ).to_dict())
        msg = f"  ⏭️  [{rule_id}] {rule_name} — PULADO: {reason}"
        self._print(f"  {self._c('GREY')}{msg}{self._c('RESET')}")
        self._file_logger.info(msg)

    # ── Mensagens genéricas ────────────────────────────────────────────────

    def info(self, msg: str) -> None:
        self._print(f"  {self._c('WHITE')}{msg}{self._c('RESET')}")
        self._file_logger.info(msg)

    def warning(self, msg: str) -> None:
        self._print(f"  {self._c('YELLOW')}⚠  {msg}{self._c('RESET')}")
        self._file_logger.warning(msg)

    def error(self, msg: str) -> None:
        self._print(f"  {self._c('RED')}✖  {msg}{self._c('RESET')}")
        self._file_logger.error(msg)

    def debug(self, msg: str) -> None:
        self._file_logger.debug(msg)

    # ── Internos ──────────────────────────────────────────────────────────

    def _c(self, color: str) -> str:
        return self._COLORS.get(color, "") if self._use_color else ""

    def _print(self, msg: str) -> None:
        print(msg)

    def _write_header(self) -> None:
        self._print(f"""
{self._c('CYAN')}╔══════════════════════════════════════════════════════════════════════╗
║        🔍  {TOOL_NAME:<44}  ║
║        v{TOOL_VERSION:<58}  ║
║        Autor : {TOOL_AUTHOR:<52}  ║
╚══════════════════════════════════════════════════════════════════════╝{self._c('RESET')}
  {self._c('GREY')}Data/Hora : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
  Host      : {socket.gethostname()}
  SO        : {platform.system()} {platform.release()}
  Python    : {sys.version.split()[0]}{self._c('RESET')}
""")


# ---------------------------------------------------------------------------
# Decorator – cronometra e loga qualquer callable de regra
# ---------------------------------------------------------------------------

def log_rule(rule_id: str, rule_name: str) -> Callable:
    """
    Decorator que envolve o método `validate` de uma regra com logging
    automático de início/fim, duração e contagem de violações.

    Uso:
        @log_rule("R01", "Excesso de parâmetros")
        def validate(self, source, lines, report): ...
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(self_rule, source: str, lines: list, report: Any) -> None:
            logger = ValidatorLogger()
            violations_before = len(report.violations)
            start_ts = logger.log_rule_start(rule_id, rule_name)
            try:
                fn(self_rule, source, lines, report)
                new_violations = len(report.violations) - violations_before
                logger.log_rule_end(rule_id, rule_name, start_ts, new_violations)
            except Exception as exc:
                detail = traceback.format_exc()
                logger.log_rule_end(
                    rule_id, rule_name, start_ts,
                    violations=0, error=str(exc),
                )
                logger.error(f"Exceção na regra {rule_id}: {exc}")
                logger.debug(detail)
                raise
        return wrapper
    return decorator


# Instância global (acesso conveniente)
logger: ValidatorLogger = ValidatorLogger()
