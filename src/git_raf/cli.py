"""git-raf CLI entry point. Provides `git raf <subcommand>` interface."""

from __future__ import annotations

import click

from git_raf import __version__
from git_raf.config import RAFConfig
from git_raf.git_ops import GitError, current_branch, git_root, head_hash, is_git_repo


def require_git_repo() -> None:
    """Exit with error if not inside a git repo."""
    if not is_git_repo():
        raise click.ClickException("Not a git repository. Run 'git init' first.")


def require_raf_init() -> None:
    """Exit with error if RAF is not initialized."""
    root = git_root()
    if not RAFConfig.is_initialized(root):
        raise click.ClickException(
            "RAF not initialized. Run 'git raf init' first."
        )


@click.group()
@click.version_option(__version__, prog_name="git-raf")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """Git Regulation As Firmware - governance-integrated version control."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


# ── Phase 1 commands ──────────────────────────────────────────────────────────


@main.command()
@click.option(
    "--governance-level",
    type=click.Choice(["minimal", "moderate", "standard", "high", "maximum"]),
    default="standard",
    help="Default governance level for the repository.",
)
def init(governance_level: str) -> None:
    """Initialize RAF in the current git repository."""
    require_git_repo()
    root = git_root()

    if RAFConfig.is_initialized(root):
        click.echo("RAF is already initialized in this repository.")
        return

    config_path = RAFConfig.init(root)
    click.echo(f"RAF initialized. Config written to {config_path}")
    click.echo(f"Default governance level: {governance_level}")


@main.command()
def status() -> None:
    """Show RAF governance status for the current repository."""
    require_git_repo()
    root = git_root()

    click.echo(f"Repository: {root.name}")

    try:
        branch = current_branch()
        click.echo(f"Branch:     {branch}")
    except GitError:
        click.echo("Branch:     (no commits yet)")
        branch = None

    try:
        commit_hash = head_hash(short=True)
        click.echo(f"HEAD:       {commit_hash}")
    except GitError:
        click.echo("HEAD:       (no commits)")

    if not RAFConfig.is_initialized(root):
        click.echo("\nRAF: not initialized (run 'git raf init')")
        return

    config = RAFConfig.load(root)
    click.echo(f"\nRAF v{__version__} initialized")
    click.echo(f"  Sinphase threshold: {config.sinphase_threshold}")
    click.echo(f"  Tag prefix:         {config.tag_prefix}")
    click.echo(f"  Tag format:         {config.tag_format}")
    click.echo(f"  Governance ref:     {config.governance_ref}")
    click.echo(f"  Entropy threshold:  {config.entropy_threshold}")

    if branch and config.branch_policies:
        # Match branch against policies
        policy = "standard"
        for pattern, level in config.branch_policies.items():
            if branch == pattern or branch.startswith(pattern + "/") or branch.startswith(pattern):
                policy = level
                break
        click.echo(f"  Branch policy:      {policy}")


# ── Phase 2 commands (sinphase, tagging, validate) ───────────────────────────


@main.command()
@click.option("--sinphase-override", type=float, default=None,
              help="Manual sinphase value (skips calculation).")
@click.option("--dry-run", is_flag=True, help="Show what would be tagged without creating it.")
def tag(sinphase_override: float | None, dry_run: bool) -> None:
    """Auto-tag based on sinphase stability metric."""
    require_git_repo()
    require_raf_init()

    from git_raf.sinphase import SinphaseResult, calculate_sinphase, classify_stability
    from git_raf.versioning import determine_bump, format_tag, get_current_version, bump
    from git_raf.governance import generate_metadata, format_tag_message

    root = git_root()
    config = RAFConfig.load(root)

    # Calculate or override sinphase
    if sinphase_override is not None:
        sinphase_val = sinphase_override
        click.echo(f"Using sinphase override: {sinphase_val}")
    else:
        result = calculate_sinphase(config.artifact_patterns, root)
        if result is None:
            raise click.ClickException(
                "Cannot calculate sinphase (no test results or artifacts found). "
                "Use --sinphase-override to provide a manual value."
            )
        sinphase_val = result.value
        click.echo(f"Sinphase: {sinphase_val:.4f} "
                    f"(artifacts: {result.artifact_count}, "
                    f"tests: {result.tests_passed}/{result.tests_total})")

    if sinphase_val < config.sinphase_threshold:
        raise click.ClickException(
            f"Sinphase {sinphase_val:.4f} below threshold "
            f"{config.sinphase_threshold}. Tagging aborted."
        )

    stability = classify_stability(sinphase_val)
    bump_level = determine_bump(root, config.version_bump_rules)
    current = get_current_version()
    new_version = bump(current, bump_level)
    tag_name = format_tag(config.tag_prefix, str(new_version), stability, config.tag_format)

    metadata = generate_metadata(
        stability=stability,
        sinphase=sinphase_val,
        version=str(new_version),
        artifact_patterns=config.artifact_patterns,
        governance_ref=config.governance_ref,
        root=root,
    )
    message = format_tag_message(stability, sinphase_val, str(new_version), metadata)

    if dry_run:
        click.echo(f"\n[DRY RUN] Would create tag: {tag_name}")
        click.echo(f"Stability: {stability}")
        click.echo(f"Version:   {new_version}")
        click.echo(f"\nTag message:\n{message}")
        return

    from git_raf.git_ops import create_tag as git_create_tag
    git_create_tag(tag_name, message)

    click.echo(f"\nCreated tag: {tag_name}")
    click.echo(f"Stability:  {stability}")
    click.echo(f"Version:    {new_version}")


@main.command()
@click.option("--strict", is_flag=True, help="Enforce strict policy validation.")
def validate(strict: bool) -> None:
    """Validate staged changes against governance policies."""
    require_git_repo()
    require_raf_init()

    from git_raf.git_ops import staged_files
    from git_raf.policy import get_branch_policy, validate_for_policy

    root = git_root()
    config = RAFConfig.load(root)

    files = staged_files()
    if not files:
        click.echo("No staged changes to validate.")
        return

    try:
        branch = current_branch()
    except GitError:
        branch = "main"

    policy = get_branch_policy(branch, config.branch_policies)
    click.echo(f"Branch: {branch} (policy: {policy})")
    click.echo(f"Staged files: {len(files)}")

    failures = validate_for_policy(policy, files, strict=strict)
    if failures:
        for msg in failures:
            click.echo(f"  FAIL: {msg}", err=True)
        raise click.ClickException(f"Validation failed with {len(failures)} issue(s).")

    click.echo("Validation passed.")


# ── Phase 3 commands (crypto, seal, verify, commit, keygen) ──────────────────


@main.command()
@click.option("--output-dir", type=click.Path(), default=None,
              help="Directory to store keys (default: ~/.raf/keys/).")
def keygen(output_dir: str | None) -> None:
    """Generate Ed25519 keypair for governance signing."""
    from git_raf.crypto import generate_keypair

    out = generate_keypair(output_dir)
    click.echo(f"Ed25519 keypair generated:")
    click.echo(f"  Private key: {out['private']}")
    click.echo(f"  Public key:  {out['public']}")


@main.command("commit")
@click.option("-m", "--message", required=True, help="Commit message.")
@click.option("-S", "--sign", is_flag=True, help="Sign commit with AuraSeal.")
@click.option("--policy-tag",
              type=click.Choice(["stable", "minor", "breaking", "experimental"]),
              default="stable", help="Policy tag for this commit.")
def raf_commit(message: str, sign: bool, policy_tag: str) -> None:
    """Create a governance-enhanced git commit."""
    require_git_repo()
    require_raf_init()

    from git_raf.governance import generate_commit_trailers
    from git_raf.git_ops import staged_files, commit as git_commit

    root = git_root()
    config = RAFConfig.load(root)

    files = staged_files()
    if not files:
        raise click.ClickException("Nothing staged to commit. Use 'git add' first.")

    trailers = generate_commit_trailers(
        policy_tag=policy_tag,
        governance_ref=config.governance_ref,
        staged_files=files,
        root=root,
        sign=sign,
    )

    full_message = f"{message}\n\n{trailers}"
    commit_hash = git_commit(full_message)
    click.echo(f"[RAF commit {commit_hash[:8]}] {message}")
    click.echo(f"  Policy-Tag: {policy_tag}")
    if sign:
        click.echo("  AuraSeal: applied")


@main.command()
@click.option("--commit-ref", default="HEAD", help="Commit to seal (default: HEAD).")
def seal(commit_ref: str) -> None:
    """Generate AuraSeal attestation for a commit."""
    require_git_repo()
    require_raf_init()

    from git_raf.crypto import generate_aura_seal_for_commit

    root = git_root()
    config = RAFConfig.load(root)
    seal_value = generate_aura_seal_for_commit(commit_ref, config, root)
    click.echo(f"AuraSeal for {commit_ref}: {seal_value}")


@main.command()
@click.option("--commit-ref", default="HEAD", help="Commit to verify (default: HEAD).")
def verify(commit_ref: str) -> None:
    """Verify AuraSeal on a commit."""
    require_git_repo()
    require_raf_init()

    from git_raf.crypto import verify_aura_seal_for_commit

    root = git_root()
    config = RAFConfig.load(root)
    result = verify_aura_seal_for_commit(commit_ref, config, root)

    if result["valid"]:
        click.echo(f"AuraSeal VERIFIED for {commit_ref}")
        click.echo(f"  Entropy-Checksum: {result['entropy_checksum']}")
        click.echo(f"  Timestamp:        {result['timestamp']}")
    else:
        click.echo(f"AuraSeal INVALID for {commit_ref}: {result['reason']}", err=True)
        raise click.ClickException("Seal verification failed.")


# ── Phase 4 commands (hooks, audit) ──────────────────────────────────────────


@main.command("install-hooks")
def install_hooks() -> None:
    """Install git hooks for RAF governance enforcement."""
    require_git_repo()
    require_raf_init()

    from git_raf.hooks import install_all_hooks

    root = git_root()
    installed = install_all_hooks(root)
    for hook_name in installed:
        click.echo(f"Installed hook: {hook_name}")
    click.echo("Git hooks installed successfully.")


@main.command()
@click.option("--from-date", default=None, help="Start date (YYYY-MM-DD).")
@click.option("--to-date", default=None, help="End date (YYYY-MM-DD).")
def audit(from_date: str | None, to_date: str | None) -> None:
    """Display governance audit trail."""
    require_git_repo()
    require_raf_init()

    from git_raf.audit import read_audit_log, format_audit_report

    root = git_root()
    records = read_audit_log(root, from_date=from_date, to_date=to_date)

    if not records:
        click.echo("No audit records found.")
        return

    report = format_audit_report(records)
    click.echo(report)


@main.command()
@click.option("--commit-ref", default="HEAD", help="Commit to rollback.")
@click.option("--reason", required=True, help="Reason for rollback.")
def rollback(commit_ref: str, reason: str) -> None:
    """Execute policy-triggered rollback."""
    require_git_repo()
    require_raf_init()

    click.echo(f"Rolling back {commit_ref}: {reason}")
    from git_raf.git_ops import _run
    _run(["revert", "--no-edit", commit_ref])
    click.echo(f"Rollback complete. Reverted {commit_ref}.")
