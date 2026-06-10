"""URLGuard CLI — score URLs from the command line."""

import logging

import typer

from app.model import scorer

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = typer.Typer(
    name="urlguard",
    help="URLGuard — Phishing URL Classifier\n\n"
    "Assess a URL as PHISHING or LEGITIMATE using a trained Random Forest model.\n"
    "Example: python cli.py \"https://suspicious-url.com/login\"",
    add_completion=False,
)


def _ensure_model() -> bool:
    if not scorer.is_loaded():
        loaded = scorer.load_model()
        if not loaded:
            typer.secho(
                "Model not found. Run 'python scripts/train.py' first.",
                fg=typer.colors.RED,
                err=True,
            )
            return False
    return True


def _print_header():
    typer.echo("╔══════════════════════════════════════════════════╗")
    typer.echo("║  URLGuard Risk Assessment                        ║")
    typer.echo("╠══════════════════════════════════════════════════╣")


def _print_footer():
    typer.echo("╚══════════════════════════════════════════════════╝")


def _run_assessment(url: str) -> int:
    if not url.startswith(("http://", "https://")):
        typer.secho(
            "Error: URL must start with http:// or https://",
            fg=typer.colors.RED,
            err=True,
        )
        return 2

    result = scorer.score_url(url)
    is_phishing = result.label == "PHISHING"

    _print_header()
    display_url = url if len(url) <= 60 else url[:57] + "..."
    typer.echo(f"║  URL:    {display_url:<45} ║")
    if is_phishing:
        typer.secho(
            "║  Label:  \U000026a0  PHISHING                          ║",
            fg=typer.colors.RED,
            bold=True,
        )
    else:
        typer.secho(
            "║  Label:  \u2713  LEGITIMATE                        ║",
            fg=typer.colors.GREEN,
            bold=True,
        )
    score_str = f"{result.risk_score:.2f}"
    typer.echo(
        f"║  Score:  {score_str}  ({result.confidence} confidence)            "
        f" ║"
    )
    if result.top_features:
        typer.echo("╠══════════════════════════════════════════════════╣")
        typer.echo("║  Top contributing features:                      ║")
        for tf in result.top_features:
            sign = "+" if tf.shap_value > 0 else "-"
            icon = "\U0001f480" if tf.direction == "phishing" else "\u2705"
            typer.echo(
                f"║  {sign} {tf.feature:<22} \u2192  {tf.shap_value:+.4f} "
                f"({icon} {tf.direction})  ║"
            )
    _print_footer()
    return 1 if is_phishing else 0


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    url: str = typer.Argument(None, help="The URL to assess"),
):
    """Assess a URL as PHISHING or LEGITIMATE."""
    if ctx.invoked_subcommand is not None:
        return
    if url is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(code=0)
    if not _ensure_model():
        raise typer.Exit(code=2)
    exit_code = _run_assessment(url)
    raise typer.Exit(code=exit_code)


if __name__ == "__main__":
    app()
