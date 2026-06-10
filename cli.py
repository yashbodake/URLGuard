"""URLGuard CLI — score URLs from the command line."""

import logging
import sys

import typer

from app.model import scorer

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

cli = typer.Typer(
    name="urlguard",
    help="URLGuard — Phishing URL Classifier",
    add_completion=False,
)


def _ensure_model() -> bool:
    """Try to load model if not already loaded. Return True if ready."""
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


def _box() -> str:
    """Return the box-drawing character set for the output frame."""
    return "╔╗╚╝║═"


def _print_header():
    """Print the assessment header box."""
    typer.echo("╔══════════════════════════════════════════════════╗")
    typer.echo("║  URLGuard Risk Assessment                        ║")
    typer.echo("╠══════════════════════════════════════════════════╣")


def _print_footer():
    """Print the assessment footer box."""
    typer.echo("╚══════════════════════════════════════════════════╝")


@cli.command()
def assess(
    url: str = typer.Argument(
        ...,
        help="The URL to assess (must start with http:// or https://)",
    ),
):
    """Assess a single URL and print a risk report."""
    if not _ensure_model():
        raise typer.Exit(code=2)

    if not url.startswith(("http://", "https://")):
        typer.secho(
            "Error: URL must start with http:// or https://",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=2)

    result = scorer.score_url(url)

    is_phishing = result.label == "PHISHING"

    # Print header
    _print_header()

    # URL line (truncated if too long)
    display_url = url if len(url) <= 60 else url[:57] + "..."
    typer.echo(f"║  URL:    {display_url:<45} ║")

    # Label line — coloured
    if is_phishing:
        typer.secho(
            f"║  Label:  \U000026a0  PHISHING                          ║",
            fg=typer.colors.RED,
            bold=True,
        )
    else:
        typer.secho(
            f"║  Label:  \u2713  LEGITIMATE                        ║",
            fg=typer.colors.GREEN,
            bold=True,
        )

    # Score line
    score_str = f"{result.risk_score:.2f}"
    typer.echo(
        f"║  Score:  {score_str}  ({result.confidence} confidence)            "
        f" ║"
    )

    # Top features
    if result.top_features:
        typer.echo("╠══════════════════════════════════════════════════╣")
        typer.echo("║  Top contributing features:                      ║")
        for tf in result.top_features:
            sign = "+" if tf.shap_value > 0 else "-"
            direction_icon = "\U0001f480" if tf.direction == "phishing" else "\u2705"
            typer.echo(
                f"║  {sign} {tf.feature:<22} \u2192  {tf.shap_value:+.4f} "
                f"({direction_icon} {tf.direction})  ║"
            )

    _print_footer()

    # Exit with code
    raise typer.Exit(code=1 if is_phishing else 0)


@cli.command()
def version():
    """Show the version number."""
    typer.echo("URLGuard v0.1.0")


if __name__ == "__main__":
    cli()
