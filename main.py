"""KOMPAS Clinical Reasoning Agent.

Entry point providing both a CLI and a FastAPI server. Turns anonymized case text
into a structured KOMPAS report using the OpenAI Agents SDK.

Usage (see README.md):
  uv run python main.py --file data/sample_case.txt      # CLI, read from file
  cat data/sample_case.txt | uv run python main.py        # CLI, read from stdin
  PORT=8000 uv run python main.py                         # API server
"""

from __future__ import annotations

import argparse
import io
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load secrets: prefer .env.local, then fall back to .env / real environment.
_ROOT = Path(__file__).resolve().parent
load_dotenv(_ROOT / ".env.local")
load_dotenv(_ROOT / ".env")
load_dotenv()

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
PROMPT_PATH = _ROOT / "prompt.md"


# --------------------------------------------------------------------------- #
# Structured report schema (mirrors the report structure in prompt.md)
# --------------------------------------------------------------------------- #
class Hypothese(BaseModel):
    hypothese: str = Field(description="De klinische hypothese of werkhypothese.")
    ondersteunende_bevindingen: list[str] = Field(
        description="Bevindingen die de hypothese ondersteunen."
    )
    nuancerende_bevindingen: list[str] = Field(
        description="Bevindingen die de hypothese nuanceren of tegenspreken."
    )
    status: str = Field(
        description="Bijv. 'werkhypothese', 'onvoldoende onderbouwd', 'minder waarschijnlijk'."
    )


class BehandelmatrixItem(BaseModel):
    onderhoudend_mechanisme: str
    verandermechanisme: str
    interventie: str = Field(description="Passende evidence-based interventie(s).")


class KompasReport(BaseModel):
    samenvatting: str = Field(description="Samenvatting van de beschikbare gegevens.")
    centrale_klinische_vraag: str
    hypothesen: list[Hypothese]
    integratieve_casusconceptualisatie: str = Field(
        description="Biopsychosociale casusconceptualisatie."
    )
    onderhoudende_mechanismen: list[str]
    kompas_behandelmatrix: list[BehandelmatrixItem]
    behandelindicatie: str = Field(description="Behandelindicatie met klinische afweging.")
    prognostische_en_beschermende_factoren: list[str]
    ontbrekende_informatie: list[str] = Field(
        description="Ontbrekende informatie en aandachtspunten (o.a. onderwerpen die "
        "menselijke beoordeling vereisen)."
    )


class AnalyzeRequest(BaseModel):
    case_text: str


# --------------------------------------------------------------------------- #
# Agent
# --------------------------------------------------------------------------- #
def _load_instructions() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return "Je bent een psychotherapeutisch redeneer- en rapportage-instrument (KOMPAS)."


def build_agent():
    # Imported lazily so that --help and other non-analyzing paths work without
    # requiring an API key or network access.
    from agents import Agent

    return Agent(
        name="KOMPAS Clinical Reasoning Agent",
        instructions=_load_instructions(),
        model=DEFAULT_MODEL,
        output_type=KompasReport,
    )


def analyze_sync(case_text: str) -> KompasReport:
    from agents import Runner

    result = Runner.run_sync(build_agent(), case_text)
    return result.final_output


async def analyze_async(case_text: str) -> KompasReport:
    from agents import Runner

    result = await Runner.run(build_agent(), case_text)
    return result.final_output


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def render_text(report: KompasReport) -> str:
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("KOMPAS-RAPPORT")
    lines.append("=" * 72)
    lines.append("\n## Samenvatting van de beschikbare gegevens")
    lines.append(report.samenvatting)
    lines.append("\n## Centrale klinische vraag")
    lines.append(report.centrale_klinische_vraag)

    lines.append("\n## Klinische hypothesen & hypothesetoetsing")
    for i, h in enumerate(report.hypothesen, 1):
        lines.append(f"\n{i}. {h.hypothese}  [{h.status}]")
        lines.append("   Ondersteunend:")
        lines.extend(f"     - {x}" for x in h.ondersteunende_bevindingen)
        lines.append("   Nuancerend:")
        lines.extend(f"     - {x}" for x in h.nuancerende_bevindingen)

    lines.append("\n## Integratieve casusconceptualisatie")
    lines.append(report.integratieve_casusconceptualisatie)

    lines.append("\n## Onderhoudende mechanismen")
    lines.extend(f"  - {x}" for x in report.onderhoudende_mechanismen)

    lines.append("\n## KOMPAS-behandelmatrix")
    for item in report.kompas_behandelmatrix:
        lines.append(f"  - Mechanisme: {item.onderhoudend_mechanisme}")
        lines.append(f"    Verandermechanisme: {item.verandermechanisme}")
        lines.append(f"    Interventie: {item.interventie}")

    lines.append("\n## Behandelindicatie met klinische afweging")
    lines.append(report.behandelindicatie)

    lines.append("\n## Prognostische en beschermende factoren")
    lines.extend(f"  - {x}" for x in report.prognostische_en_beschermende_factoren)

    lines.append("\n## Ontbrekende informatie en aandachtspunten")
    lines.extend(f"  - {x}" for x in report.ontbrekende_informatie)

    return "\n".join(lines)


def build_docx(report: KompasReport) -> bytes:
    from docx import Document

    doc = Document()
    doc.add_heading("KOMPAS-rapport", level=0)

    doc.add_heading("Samenvatting van de beschikbare gegevens", level=1)
    doc.add_paragraph(report.samenvatting)

    doc.add_heading("Centrale klinische vraag", level=1)
    doc.add_paragraph(report.centrale_klinische_vraag)

    doc.add_heading("Klinische hypothesen & hypothesetoetsing", level=1)
    for i, h in enumerate(report.hypothesen, 1):
        doc.add_heading(f"{i}. {h.hypothese} [{h.status}]", level=2)
        doc.add_paragraph("Ondersteunende bevindingen:")
        for x in h.ondersteunende_bevindingen:
            doc.add_paragraph(x, style="List Bullet")
        doc.add_paragraph("Nuancerende bevindingen:")
        for x in h.nuancerende_bevindingen:
            doc.add_paragraph(x, style="List Bullet")

    doc.add_heading("Integratieve casusconceptualisatie", level=1)
    doc.add_paragraph(report.integratieve_casusconceptualisatie)

    doc.add_heading("Onderhoudende mechanismen", level=1)
    for x in report.onderhoudende_mechanismen:
        doc.add_paragraph(x, style="List Bullet")

    doc.add_heading("KOMPAS-behandelmatrix", level=1)
    for item in report.kompas_behandelmatrix:
        doc.add_paragraph(
            f"{item.onderhoudend_mechanisme} → {item.verandermechanisme}: {item.interventie}",
            style="List Bullet",
        )

    doc.add_heading("Behandelindicatie met klinische afweging", level=1)
    doc.add_paragraph(report.behandelindicatie)

    doc.add_heading("Prognostische en beschermende factoren", level=1)
    for x in report.prognostische_en_beschermende_factoren:
        doc.add_paragraph(x, style="List Bullet")

    doc.add_heading("Ontbrekende informatie en aandachtspunten", level=1)
    for x in report.ontbrekende_informatie:
        doc.add_paragraph(x, style="List Bullet")

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# --------------------------------------------------------------------------- #
# FastAPI app
# --------------------------------------------------------------------------- #
def create_app():
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import Response

    app = FastAPI(title="KOMPAS Clinical Reasoning Agent", version="0.1.0")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/analyze")
    async def analyze(req: AnalyzeRequest):
        if not req.case_text.strip():
            raise HTTPException(status_code=400, detail="case_text mag niet leeg zijn.")
        report = await analyze_async(req.case_text)
        return report.model_dump()

    @app.post("/analyze/docx")
    async def analyze_docx(req: AnalyzeRequest):
        if not req.case_text.strip():
            raise HTTPException(status_code=400, detail="case_text mag niet leeg zijn.")
        report = await analyze_async(req.case_text)
        data = build_docx(report)
        return Response(
            content=data,
            media_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
            headers={"Content-Disposition": 'attachment; filename="kompas-rapport.docx"'},
        )

    return app


# Module-level ASGI app so `uvicorn main:app` also works.
app = None


def _get_app():
    global app
    if app is None:
        app = create_app()
    return app


def run_server() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "127.0.0.1")
    uvicorn.run(_get_app(), host=host, port=port)


def run_cli(case_text: str) -> None:
    if not case_text.strip():
        print("Geen casustekst ontvangen. Gebruik --file of pipe tekst via stdin.", file=sys.stderr)
        raise SystemExit(2)
    report = analyze_sync(case_text)
    print(render_text(report))


def cli() -> None:
    parser = argparse.ArgumentParser(description="KOMPAS Clinical Reasoning Agent")
    parser.add_argument("--file", "-f", help="Pad naar een bestand met (geanonimiseerde) casustekst.")
    parser.add_argument("--serve", action="store_true", help="Start de API-server.")
    args = parser.parse_args()

    if args.file:
        run_cli(Path(args.file).read_text(encoding="utf-8"))
        return

    if not sys.stdin.isatty():
        data = sys.stdin.read()
        if data.strip():
            run_cli(data)
            return

    # No CLI input provided: run the API server (honoring PORT / --serve).
    run_server()


if __name__ == "__main__":
    cli()
