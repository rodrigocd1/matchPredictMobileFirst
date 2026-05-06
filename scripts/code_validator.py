"""
code_validator.py
=================
Universal Code Validator — execução fail-fast regra a regra.

Cada regra é executada em sequência. Caso qualquer regra encontre
violações, o pipeline é interrompido imediatamente e as regras
subsequentes são marcadas como SKIPPED no log.

Padrões : Strategy · Composite · Builder · Facade · Chain-of-Responsibility
Ref.    : Clean Code (Robert C. Martin), Defensive Programming

Autor   : Code Quality Guardian
Versão  : 2.0.0
"""

from __future__ import annotations

import re
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from validator_logger import ValidatorLogger, log_rule, logger


# ---------------------------------------------------------------------------
# Value Objects
# ---------------------------------------------------------------------------

class Severity(Enum):
    WARNING = "WARNING"
    ERROR   = "ERROR"
    INFO    = "INFO"


@dataclass(frozen=True)
class Violation:
    rule_id  : str
    severity : Severity
    line     : int
    message  : str

    def __str__(self) -> str:
        icon = "⚠️ " if self.severity == Severity.WARNING else "❌"
        return f"    Linha {self.line:>4} | {icon} {self.severity.value} | [{self.rule_id}] {self.message}"


@dataclass
class ValidationReport:
    file_path  : Path
    violations : list[Violation] = field(default_factory=list)
    aborted_at : str = ""

    def add(self, violation: Violation) -> None:
        self.violations.append(violation)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)

    def print_summary(self) -> None:
        sep = "─" * 70
        print(f"\n{sep}")
        print(f"  Arquivo : {self.file_path}")
        print(f"  Total   : {len(self.violations)} ocorrência(s)")
        if self.aborted_at:
            print(f"  🛑 Pipeline cancelado na regra : {self.aborted_at}")
        print(sep)
        if not self.has_violations:
            print("  ✅  Nenhuma violação encontrada. Bom trabalho!")
        else:
            for v in sorted(self.violations, key=lambda x: x.line):
                print(v)
        print()


# ---------------------------------------------------------------------------
# Source Sanitizer
# ---------------------------------------------------------------------------

class SourceSanitizer:
    """Remove comentários e strings do código-fonte para evitar falsos-positivos."""

    _LINE_COMMENT  = re.compile(r'(//[^\n]*|#[^\n]*)')
    _BLOCK_COMMENT = re.compile(r'/\*.*?\*/', re.DOTALL)
    _DOUBLE_STRING = re.compile(r'"(?:\\.|[^"\\])*"')
    _SINGLE_STRING = re.compile(r"'(?:\\.|[^'\\])*'")
    _TEMPLATE_STR  = re.compile(r'`(?:\\.|[^`\\])*`', re.DOTALL)

    @classmethod
    def strip_comments_and_strings(cls, source: str) -> str:
        s = cls._BLOCK_COMMENT.sub('/* */', source)
        s = cls._LINE_COMMENT.sub('//', s)
        s = cls._TEMPLATE_STR.sub('``', s)
        s = cls._DOUBLE_STRING.sub('""', s)
        s = cls._SINGLE_STRING.sub("''", s)
        return s

    @classmethod
    def strip_comments_only(cls, source: str) -> str:
        s = cls._BLOCK_COMMENT.sub('/* */', source)
        s = cls._LINE_COMMENT.sub('//', s)
        return s


# ---------------------------------------------------------------------------
# Excecao de cancelamento de pipeline
# ---------------------------------------------------------------------------

class PipelineAbortError(Exception):
    """Lancada pelo RuleSet para interromper a cadeia de regras."""

    def __init__(self, rule_id: str, violations: int) -> None:
        super().__init__(
            f"Pipeline abortado na regra {rule_id} com {violations} violacao(oes)."
        )
        self.rule_id    = rule_id
        self.violations = violations


# ---------------------------------------------------------------------------
# Strategy - Interface base
# ---------------------------------------------------------------------------

class ValidationRule(ABC):
    """Contrato base para todas as regras de validacao."""

    @property
    @abstractmethod
    def rule_id(self) -> str: ...

    @property
    @abstractmethod
    def rule_name(self) -> str: ...

    @abstractmethod
    def validate(self, source: str, lines: list[str], report: ValidationReport) -> None: ...

    @staticmethod
    def _find_line(lines: list[str], char_pos: int) -> int:
        accumulated = 0
        for idx, line in enumerate(lines, start=1):
            accumulated += len(line) + 1
            if char_pos < accumulated:
                return idx
        return len(lines)


# ---------------------------------------------------------------------------
# Regra 1 - Excesso de parametros
# ---------------------------------------------------------------------------

class ExcessiveParametersRule(ValidationRule):
    """Metodos com mais de 3 parametros de entrada."""

    _MAX_PARAMS     = 3
    _METHOD_PATTERN = re.compile(
        r'\b(?:function\s+)?(\w+)\s*\(([^)]{0,500})\)',
        re.MULTILINE,
    )

    @property
    def rule_id(self) -> str:
        return "R01"

    @property
    def rule_name(self) -> str:
        return "Excesso de parametros (> 3)"

    @log_rule("R01", "Excesso de parametros (> 3)")
    def validate(self, source: str, lines: list[str], report: ValidationReport) -> None:
        cleaned = SourceSanitizer.strip_comments_and_strings(source)
        for match in self._METHOD_PATTERN.finditer(cleaned):
            method_name = match.group(1)
            params_raw  = match.group(2).strip()
            if not params_raw:
                continue
            count = self._count_params(params_raw)
            if count > self._MAX_PARAMS:
                report.add(Violation(
                    rule_id  = self.rule_id,
                    severity = Severity.WARNING,
                    line     = self._find_line(lines, match.start()),
                    message  = (
                        f"O metodo `{method_name}` possui {count} parametros. "
                        "Mais de 3 parametros - e necessario refatorar."
                    ),
                ))

    @staticmethod
    def _count_params(raw: str) -> int:
        depth, count = 0, 1
        for ch in raw:
            if ch in '([{':
                depth += 1
            elif ch in ')]}':
                depth -= 1
            elif ch == ',' and depth == 0:
                count += 1
        return count


# ---------------------------------------------------------------------------
# Regra 2 - Parametro sem validacao de null
# ---------------------------------------------------------------------------

class MissingNullCheckRule(ValidationRule):
    """Parametros sem validacao de null/blank/empty."""

    _METHOD_PATTERN = re.compile(
        r'\b(?:function\s+)?(\w+)\s*\(([^)]{1,500})\)\s*\{',
        re.MULTILINE,
    )
    _NULL_CHECK = re.compile(
        r'\b(!=\s*null|Objects\.requireNonNull|isBlank|isEmpty|'
        r'StringUtils\.isEmpty|StringUtils\.isBlank|'
        r'!= None|is not None|== null|== None)\b',
        re.IGNORECASE,
    )
    _SKIP_TOKENS = frozenset({
        'int','long','double','float','boolean','bool','string','String',
        'void','var','let','const','final','static','public','private',
        'protected','override','async','def','self','cls','new','return',
        'Integer','Long','Double','Float','Boolean','Object','List','Map',
        'Set','Array','ArrayList','HashMap','HashSet','Optional','type',
    })

    @property
    def rule_id(self) -> str:
        return "R02"

    @property
    def rule_name(self) -> str:
        return "Parametro sem validacao de null"

    @log_rule("R02", "Parametro sem validacao de null")
    def validate(self, source: str, lines: list[str], report: ValidationReport) -> None:
        cleaned = SourceSanitizer.strip_comments_and_strings(source)
        for m in self._METHOD_PATTERN.finditer(cleaned):
            params_raw  = m.group(2).strip()
            method_name = m.group(1)
            if not params_raw:
                continue
            body   = self._extract_body(cleaned, m.end())
            params = self._extract_param_names(params_raw)
            for param in params:
                if param.lower() in self._SKIP_TOKENS:
                    continue
                if not self._has_null_check(body, param):
                    report.add(Violation(
                        rule_id  = self.rule_id,
                        severity = Severity.WARNING,
                        line     = self._find_line(lines, m.start()),
                        message  = (
                            f"O parametro `{param}` do metodo `{method_name}` "
                            "nao tem validacao de null/blank/empty."
                        ),
                    ))

    def _extract_param_names(self, raw: str) -> list[str]:
        names = []
        for seg in raw.split(','):
            tokens = seg.strip().split()
            if tokens:
                candidate = re.sub(r'[^a-zA-Z0-9_]', '', tokens[-1])
                if candidate and candidate not in self._SKIP_TOKENS:
                    names.append(candidate)
        return names

    @staticmethod
    def _extract_body(source: str, start: int) -> str:
        depth, idx = 1, start
        while idx < len(source) and depth > 0:
            if   source[idx] == '{': depth += 1
            elif source[idx] == '}': depth -= 1
            idx += 1
        return source[start:idx]

    def _has_null_check(self, body: str, param: str) -> bool:
        return any(
            param in line and self._NULL_CHECK.search(line)
            for line in body.splitlines()
        )


# ---------------------------------------------------------------------------
# Regra 3 - Query fora de DAO
# ---------------------------------------------------------------------------

class QueryOutsideDaoRule(ValidationRule):
    """Query SQL/SOQL fora de classes DAO."""

    _QUERY_PATTERN = re.compile(
        r'\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN|SOQL|SOSL|'
        r'\[SELECT|Database\.query|createQuery|createNativeQuery|'
        r'executeQuery|prepareStatement)\b',
        re.IGNORECASE,
    )
    _METHOD_PATTERN = re.compile(
        r'\b(?:function\s+)?(\w+)\s*\([^)]*\)\s*\{',
        re.MULTILINE,
    )
    _DAO_PATTERN = re.compile(
        r'\b(DAO|Dao|Repository|Repo|Mapper|Gateway|Persistence)\b'
    )

    @property
    def rule_id(self) -> str:
        return "R03"

    @property
    def rule_name(self) -> str:
        return "Query fora de classe DAO"

    @log_rule("R03", "Query fora de classe DAO")
    def validate(self, source: str, lines: list[str], report: ValidationReport) -> None:
        if self._DAO_PATTERN.search(source[:500]):
            return
        cleaned = SourceSanitizer.strip_comments_only(source)
        for m in self._METHOD_PATTERN.finditer(cleaned):
            method_name = m.group(1)
            body = MissingNullCheckRule._extract_body(cleaned, m.end())
            if self._QUERY_PATTERN.search(body):
                report.add(Violation(
                    rule_id  = self.rule_id,
                    severity = Severity.WARNING,
                    line     = self._find_line(lines, m.start()),
                    message  = (
                        f"Query existe no metodo `{method_name}`. "
                        "Por favor, mova-a para uma classe DAO."
                    ),
                ))


# ---------------------------------------------------------------------------
# Regra 4 - Numero magico
# ---------------------------------------------------------------------------

class MagicNumberRule(ValidationRule):
    """Numeros magicos soltos no codigo."""

    _IMPORT_LINE = re.compile(r'^\s*(import|#include|using|package)')
    _ASSIGNMENT  = re.compile(r'(?:const|let|var|final|static|=)\s*[\w.]*\s*=?\s*\d')
    _ANNOTATION  = re.compile(r'@\w+\s*\(\s*\d')
    _LOOP_INIT   = re.compile(r'\b(for|while)\s*\(.*?\b\d+\b')

    @property
    def rule_id(self) -> str:
        return "R04"

    @property
    def rule_name(self) -> str:
        return "Numero magico"

    @log_rule("R04", "Numero magico")
    def validate(self, source: str, lines: list[str], report: ValidationReport) -> None:
        cleaned_lines = SourceSanitizer.strip_comments_and_strings(source).splitlines()
        for line_num, line in enumerate(cleaned_lines, start=1):
            if self._IMPORT_LINE.match(line):
                continue
            for match in re.finditer(r'(?<!["\w.])\b(\d+\.?\d*)\b', line):
                number = match.group(1)
                if number in {'0', '1', '2'}:
                    continue
                context = line[:match.start()].rstrip()
                if (self._ASSIGNMENT.search(context) or
                        self._ANNOTATION.search(context) or
                        self._LOOP_INIT.search(line)):
                    continue
                report.add(Violation(
                    rule_id  = self.rule_id,
                    severity = Severity.WARNING,
                    line     = line_num,
                    message  = f"Numero magico `{number}`! Coloque em uma variavel.",
                ))
                break


# ---------------------------------------------------------------------------
# Regra 5 - String magica
# ---------------------------------------------------------------------------

class MagicStringRule(ValidationRule):
    """Strings literais fora de contexto de comentario sem atribuicao."""

    _STRING_PATTERN = re.compile(r'"([^"]{4,})"')
    _ACCEPTABLE     = re.compile(
        r'(?:import|require|include|package|@|#|log\.|print|'
        r'console\.|System\.out|throw\s+new|Exception|Error|'
        r'Logger|log\b|debug|info|warn|error)\s*',
        re.IGNORECASE,
    )

    @property
    def rule_id(self) -> str:
        return "R05"

    @property
    def rule_name(self) -> str:
        return "String magica"

    @log_rule("R05", "String magica")
    def validate(self, source: str, lines: list[str], report: ValidationReport) -> None:
        no_comments = SourceSanitizer.strip_comments_only(source)
        for line_num, line in enumerate(no_comments.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith('//') or stripped.startswith('#'):
                continue
            if self._ACCEPTABLE.search(stripped):
                continue
            for match in self._STRING_PATTERN.finditer(line):
                content = match.group(1).strip()
                if re.match(r'^[/\\.]|https?://', content):
                    continue
                context = line[:match.start()].strip()
                if re.search(r'\b(const|final|val|var|let|static)\b', context):
                    continue
                report.add(Violation(
                    rule_id  = self.rule_id,
                    severity = Severity.WARNING,
                    line     = line_num,
                    message  = f'String magica! Passe `"{content[:40]}"` para uma variavel.',
                ))
                break


# ---------------------------------------------------------------------------
# Regra 6 - Variavel muito longa
# ---------------------------------------------------------------------------

class LongVariableNameRule(ValidationRule):
    """Variaveis com mais de 30 caracteres."""

    _MAX_LENGTH  = 30
    _VAR_PATTERN = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]{30,})\b')
    _SKIP_TOKENS = frozenset({
        'AbstractApplicationContext', 'IllegalArgumentException',
        'NullPointerException', 'IndexOutOfBoundsException',
        'UnsupportedOperationException',
    })

    @property
    def rule_id(self) -> str:
        return "R06"

    @property
    def rule_name(self) -> str:
        return "Variavel com nome muito longo (> 30 chars)"

    @log_rule("R06", "Variavel com nome muito longo (> 30 chars)")
    def validate(self, source: str, lines: list[str], report: ValidationReport) -> None:
        cleaned_lines = SourceSanitizer.strip_comments_and_strings(source).splitlines()
        seen: set[str] = set()
        for line_num, line in enumerate(cleaned_lines, start=1):
            for match in self._VAR_PATTERN.finditer(line):
                name = match.group(1)
                if name in self._SKIP_TOKENS or name in seen:
                    continue
                seen.add(name)
                report.add(Violation(
                    rule_id  = self.rule_id,
                    severity = Severity.WARNING,
                    line     = line_num,
                    message  = (
                        f"A variavel `{name}` esta muito grande "
                        f"({len(name)} chars). Reduza!"
                    ),
                ))


# ---------------------------------------------------------------------------
# Regra 7 - Variavel muito curta
# ---------------------------------------------------------------------------

class ShortVariableNameRule(ValidationRule):
    """Variaveis muito curtas (1 a 4 caracteres)."""

    _MIN_LENGTH  = 4
    _VAR_PATTERN = re.compile(
        r'\b(?:var|let|const|int|long|double|float|boolean|String|'
        r'Object|List|Map|Set|def|auto)\s+([a-zA-Z_]\w*)\b',
    )
    _ALLOWED = frozenset({'i', 'j', 'k', 'e', 'ex', 'err', 'id', 'ok', 'db', 'io'})

    @property
    def rule_id(self) -> str:
        return "R07"

    @property
    def rule_name(self) -> str:
        return "Variavel com nome muito curto (1-4 chars)"

    @log_rule("R07", "Variavel com nome muito curto (1-4 chars)")
    def validate(self, source: str, lines: list[str], report: ValidationReport) -> None:
        cleaned_lines = SourceSanitizer.strip_comments_and_strings(source).splitlines()
        seen: set[str] = set()
        for line_num, line in enumerate(cleaned_lines, start=1):
            for match in self._VAR_PATTERN.finditer(line):
                name = match.group(1)
                if name in seen or name in self._ALLOWED:
                    continue
                if len(name) <= self._MIN_LENGTH:
                    seen.add(name)
                    report.add(Violation(
                        rule_id  = self.rule_id,
                        severity = Severity.WARNING,
                        line     = line_num,
                        message  = f"Variavel `{name}` esta muito curta! Use nomes mais descritivos.",
                    ))


# ---------------------------------------------------------------------------
# Regra 8 - For encadeado
# ---------------------------------------------------------------------------

class NestedForRule(ValidationRule):
    """3 ou mais lacos for encadeados."""

    _FOR_OPEN = re.compile(r'\bfor\s*\(')

    @property
    def rule_id(self) -> str:
        return "R08"

    @property
    def rule_name(self) -> str:
        return "For encadeado (>= 3 niveis)"

    @log_rule("R08", "For encadeado (>= 3 niveis)")
    def validate(self, source: str, lines: list[str], report: ValidationReport) -> None:
        cleaned_lines   = SourceSanitizer.strip_comments_and_strings(source).splitlines()
        for_depth_stack: list[int] = []
        brace_depth     = 0
        first_line: Optional[int] = None

        for line_num, line in enumerate(cleaned_lines, start=1):
            for ch in line:
                if ch == '{':
                    brace_depth += 1
                elif ch == '}':
                    while for_depth_stack and for_depth_stack[-1] >= brace_depth:
                        for_depth_stack.pop()
                    brace_depth = max(brace_depth - 1, 0)
            for _ in self._FOR_OPEN.finditer(line):
                for_depth_stack.append(brace_depth)
                if len(for_depth_stack) >= 3 and first_line is None:
                    first_line = line_num

        if first_line is not None:
            report.add(Violation(
                rule_id  = self.rule_id,
                severity = Severity.ERROR,
                line     = first_line,
                message  = "For encadeado! Refaca sua logica! ❌",
            ))


# ---------------------------------------------------------------------------
# Regra 9 - If encadeado
# ---------------------------------------------------------------------------

class NestedIfRule(ValidationRule):
    """3 ou mais ifs encadeados."""

    @property
    def rule_id(self) -> str:
        return "R09"

    @property
    def rule_name(self) -> str:
        return "If encadeado (>= 3 niveis)"

    @log_rule("R09", "If encadeado (>= 3 niveis)")
    def validate(self, source: str, lines: list[str], report: ValidationReport) -> None:
        cleaned_lines = SourceSanitizer.strip_comments_and_strings(source).splitlines()
        if_depth, first_line = 0, None

        for line_num, line in enumerate(cleaned_lines, start=1):
            stripped = line.strip()
            if re.match(r'\bif\s*[\(]', stripped) or re.match(r'\bif\s+', stripped):
                if_depth += 1
                if if_depth >= 3 and first_line is None:
                    first_line = line_num
            if stripped in ('}', '};') and if_depth > 0:
                if_depth -= 1

        if first_line is not None:
            report.add(Violation(
                rule_id  = self.rule_id,
                severity = Severity.WARNING,
                line     = first_line,
                message  = "Ifs encadeados! Refaca sua logica.",
            ))


# ---------------------------------------------------------------------------
# Regra 10 - Query dentro de laco
# ---------------------------------------------------------------------------

class QueryInsideLoopRule(ValidationRule):
    """Query SQL/SOQL dentro de laco de repeticao."""

    _LOOP_KEYWORDS = re.compile(r'\b(for|while|forEach|stream|each)\b')
    _QUERY_PATTERN = re.compile(
        r'\b(SELECT|INSERT|UPDATE|DELETE|Database\.query|'
        r'createQuery|prepareStatement|executeQuery|\.find\(|\.findAll\()\b',
        re.IGNORECASE,
    )

    @property
    def rule_id(self) -> str:
        return "R10"

    @property
    def rule_name(self) -> str:
        return "Query dentro de laco"

    @log_rule("R10", "Query dentro de laco")
    def validate(self, source: str, lines: list[str], report: ValidationReport) -> None:
        cleaned_lines = SourceSanitizer.strip_comments_only(source).splitlines()
        brace_depth   = 0
        loop_depths: list[int] = []

        for line_num, line in enumerate(cleaned_lines, start=1):
            opens  = line.count('{')
            closes = line.count('}')
            if self._LOOP_KEYWORDS.search(line):
                loop_depths.append(brace_depth)
            brace_depth += opens
            if loop_depths and self._QUERY_PATTERN.search(line):
                report.add(Violation(
                    rule_id  = self.rule_id,
                    severity = Severity.ERROR,
                    line     = line_num,
                    message  = "Query dentro de Laco! Remova a query e refaca sua logica.",
                ))
            brace_depth -= closes
            brace_depth  = max(brace_depth, 0)
            loop_depths  = [d for d in loop_depths if d < brace_depth]


# ---------------------------------------------------------------------------
# Chain-of-Responsibility + Composite — RuleSet com Fail-Fast
# ---------------------------------------------------------------------------

class RuleSet:
    """
    Executa regras em sequencia com comportamento fail-fast.

    Ao encontrar qualquer violacao em uma regra:
      1. Registra a violacao no relatorio
      2. Marca regras restantes como SKIPPED no log
      3. Lanca PipelineAbortError para cancelar o pipeline
    """

    def __init__(self, rules: list[ValidationRule]) -> None:
        if not rules:
            raise ValueError("RuleSet precisa de ao menos uma regra.")
        self._rules = rules

    def validate(self, source: str, report: ValidationReport) -> None:
        lines      = source.splitlines(keepends=True)
        _logger    = ValidatorLogger()
        abort_rule : Optional[str] = None

        for rule in self._rules:
            if abort_rule is not None:
                _logger.log_rule_skipped(
                    rule.rule_id,
                    rule.rule_name,
                    reason=f"Pipeline cancelado pela regra {abort_rule}",
                )
                continue

            violations_before = len(report.violations)

            try:
                rule.validate(source, lines, report)
            except Exception as exc:
                report.aborted_at = rule.rule_id
                abort_rule        = rule.rule_id
                _logger.error(f"Erro inesperado na regra {rule.rule_id}: {exc}")
                continue

            new_violations = len(report.violations) - violations_before

            if new_violations > 0:
                report.aborted_at = rule.rule_id
                abort_rule        = rule.rule_id
                _logger.warning(
                    f"Regra {rule.rule_id} encontrou {new_violations} violacao(oes). "
                    "Pipeline cancelado — regras seguintes serao ignoradas."
                )

        if abort_rule:
            raise PipelineAbortError(abort_rule, len(report.violations))


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

class DefaultRuleSetBuilder:
    """Monta o RuleSet padrao com todas as 10 regras."""

    @staticmethod
    def build() -> RuleSet:
        return RuleSet([
            ExcessiveParametersRule(),
            MissingNullCheckRule(),
            QueryOutsideDaoRule(),
            MagicNumberRule(),
            MagicStringRule(),
            LongVariableNameRule(),
            ShortVariableNameRule(),
            NestedForRule(),
            NestedIfRule(),
            QueryInsideLoopRule(),
        ])


# ---------------------------------------------------------------------------
# Facade - CodeValidator
# ---------------------------------------------------------------------------

class CodeValidator:
    """Ponto de entrada unico. Orquestra validacao e logging de sessao."""

    def __init__(self, rule_set: Optional[RuleSet] = None) -> None:
        self._rule_set = rule_set or DefaultRuleSetBuilder.build()

    def validate_file(self, file_path: Path) -> ValidationReport:
        if not isinstance(file_path, Path):
            raise TypeError(f"Esperado Path, recebido {type(file_path).__name__}.")
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {file_path}")
        if not file_path.is_file():
            raise ValueError(f"Caminho nao e um arquivo: {file_path}")

        source = self._read_source(file_path)
        report = ValidationReport(file_path=file_path)

        logger.info(f"Analisando : {file_path.name}")

        try:
            self._rule_set.validate(source, report)
        except PipelineAbortError as abort:
            logger.warning(str(abort))

        return report

    def validate_directory(
        self,
        directory  : Path,
        extensions : Optional[list[str]] = None,
    ) -> list[ValidationReport]:
        if not directory.is_dir():
            raise ValueError(f"Nao e um diretorio valido: {directory}")

        exts = extensions or [
            '.java', '.js', '.ts', '.cs', '.cpp', '.c', '.h',
            '.hpp', '.apex', '.cls', '.py', '.kt', '.swift',
        ]
        reports = []
        for ext in exts:
            for fp in directory.rglob(f'*{ext}'):
                try:
                    reports.append(self.validate_file(fp))
                except (OSError, ValueError) as exc:
                    logger.error(f"Arquivo ignorado {fp}: {exc}")
        return reports

    @staticmethod
    def _read_source(file_path: Path) -> str:
        for enc in ('utf-8', 'latin-1', 'cp1252'):
            try:
                return file_path.read_text(encoding=enc)
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError(f"Nao foi possivel decodificar: {file_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _usage() -> None:
    print("Uso:")
    print("  python code_validator.py <arquivo_ou_diretorio> [extensoes...]")
    print("\nExemplos:")
    print("  python code_validator.py MinhaClasse.java")
    print("  python code_validator.py ./src .java .js .ts")


def main() -> None:
    if len(sys.argv) < 2:
        _usage()
        sys.exit(1)

    target     = Path(sys.argv[1])
    extensions = sys.argv[2:] or None
    validator  = CodeValidator()

    logger.begin_session(str(target))

    total_violations = 0
    files_analyzed   = 0
    aborted_at       = ""

    try:
        if target.is_file():
            report = validator.validate_file(target)
            report.print_summary()
            files_analyzed   = 1
            total_violations = len(report.violations)
            aborted_at       = report.aborted_at

        elif target.is_dir():
            reports = validator.validate_directory(target, extensions)
            for report in reports:
                report.print_summary()
                total_violations += len(report.violations)
                if report.aborted_at and not aborted_at:
                    aborted_at = report.aborted_at
            files_analyzed = len(reports)
            print(f"{'─'*70}")
            print(f"  Arquivos: {files_analyzed} | Violacoes: {total_violations}")

        else:
            logger.error(f"Caminho invalido: {target}")
            sys.exit(1)

    finally:
        logger.end_session(
            files_analyzed   = files_analyzed,
            total_violations = total_violations,
            aborted_at_rule  = aborted_at,
        )

    sys.exit(1 if total_violations > 0 else 0)


if __name__ == '__main__':
    main()
