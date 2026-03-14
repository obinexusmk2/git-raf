# git-raf

**Git Regulation As Firmware** — governance-integrated version control.

```
pip install git-raf
```

```bash
$ git raf --help
Usage: git-raf [OPTIONS] COMMAND [ARGS]...

  Git Regulation As Firmware — governance-integrated version control.

Commands:
  init           Initialize RAF in the current git repository.
  status         Show RAF governance status for the current repository.
  commit         Create a governance-enhanced git commit.
  tag            Auto-tag based on sinphase stability metric.
  validate       Validate staged changes against governance policies.
  keygen         Generate Ed25519 keypair for governance signing.
  seal           Generate AuraSeal attestation for a commit.
  verify         Verify AuraSeal on a commit.
  install-hooks  Install git hooks for RAF governance enforcement.
  audit          Display governance audit trail.
  rollback       Execute policy-triggered rollback.
```

---

## The Governance Trilogy

**Who governs the governor?**
**Who has the final say?**
**What if two policies fight?**

> In traditional systems, these questions spark politics.
> In RAF, they're settled in code.

### Problem 1: "I Am the Governor!"

In legacy dev teams, authority is vibes-based. The loudest voice gets the last word. Rules are soft suggestions. Accountability is unclear.

**RAF's answer: Regulation by Competence.** Every dev action is a cryptographic transaction. Commits are validated via `AuraSeal`, `entropy_checksum`, and `policy_tag`. You only govern what you've proven you can govern.

> Authority = verified governance compliance.
> You are trusted because **your code holds under entropy.**

### Problem 2: "Govern the Governor"

In other systems, policy authors get godmode. Nobody audits the auditors. Changes go unchecked.

**RAF's answer: Governance Is Governed.** All policy updates must pass vector-based evaluations across three dimensions — `attack_risk`, `rollback_cost`, `stability_impact`. These vectors are scored, signed, and versioned. If a policy leads to entropy drift, it gets blocked, rolled back, or rewritten.

> Even governors get governed.
> Your policy is only valid **if it survives entropy.**

### Problem 3: "Final Say When Policies Clash"

Two valid policies. One runtime path. Who wins?

**RAF's answer: Telemetry-Based Resolution.** Vector scores are compared — math wins, not ego. If still inconclusive, real-world telemetry speaks: the policy that preserves system stability wins.

| Question | RAF's Answer |
|---|---|
| "Who is the governor?" | The one with the AuraSeal + entropy-stable commit. |
| "Who governs the governors?" | The policy engine + cryptographic audit trail. |
| "Who has the final say?" | Telemetry, entropy scores, rollback risk — **governance by reality check.** |

---

## Quick Start

```bash
# Initialize RAF in your repository
git raf init

# Check governance status
git raf status

# Generate signing keys
git raf keygen

# Make a governance-enhanced commit
git add .
git raf commit -m "feat(auth): add identity verification module"

# Make a signed commit with AuraSeal
git raf commit -S -m "fix(core): patch entropy drift in validation loop"

# Auto-tag based on stability metric
git raf tag --sinphase-override 0.75

# Verify AuraSeal on a commit
git raf verify

# Install pre-commit/post-commit hooks
git raf install-hooks
```

---

## Architecture

### Governance-Enhanced Commits

RAF transforms commits from file snapshots into cryptographically-signed governance transactions. Every `git raf commit` appends governance trailers to the commit message:

```
feat(auth): add identity verification module

Policy-Tag: stable
Governance-Ref: default_policy.rift.gov
Entropy-Checksum: 83e125d5be723950292bb653f567545754...
Governance-Vector: [attack_risk: 0.25, rollback_cost: 0.06, stability_impact: 0.75]
AuraSeal: ebed2f5d334f663f3e35905613b72947bf...
RAF-Timestamp: 2026-03-14T20:38:10Z
```

### Sinphase Stability Metric

The sinphase metric (ported from the original bash implementation) measures build stability as a function of artifact availability and test pass rate:

```
sigma = (artifact_count x tests_passed) / (tests_total x normalization_factor)
```

| Sinphase Range | Stability | Description |
|---|---|---|
| < 0.2 | `alpha` | Early development, unstable |
| 0.2 - 0.4 | `beta` | Feature-complete, testing |
| 0.4 - 0.6 | `rc` | Release candidate |
| 0.6 - 0.8 | `stable` | Production-ready |
| >= 0.8 | `release` | Fully validated release |

### Governance Vector

Every commit is assessed across three risk dimensions:

- **Attack Risk** — `1 - sinphase`. Higher stability = lower risk.
- **Rollback Cost** — Proportional to the scope of file changes.
- **Stability Impact** — Direct sinphase value.

### Branch Policy Hierarchy

Branches enforce governance levels of ascending strictness:

| Branch Pattern | Policy Level | Requirements |
|---|---|---|
| `experimental/*` | `minimal` | Basic checks only |
| `feature/*` | `moderate` | Semantic validation |
| `develop` | `standard` | Full policy validation |
| `release/*` | `high` | Entropy + vector analysis |
| `main` | `maximum` | AuraSeal + multi-signature |

### AuraSeal Cryptographic Attestation

AuraSeal provides tamper-evident proof that governance validation occurred:

- HMAC-SHA256 over `(entropy_checksum, timestamp, stability, version)`
- Ed25519 keypair for identity-bound signing
- SHA3-256 entropy checksums over file contents
- Independently verifiable without access to validation infrastructure

---

## HACC Proposal Governance Flow

RAF's governance model extends beyond code commits to formal proposal workflows. The diagram below illustrates the HACC (Humanitarian and Compliance Council) proposal lifecycle — from submission through evaluation to archival — with every action signed by AuraSeal and stored in an immutable governance ledger.

**Submission Phase**: A Public Advocate submits a HACC Proposal (ethical, inclusive, no-ghost policy) through the Ethical Framework Portal. Identity and timestamp are logged to the Governance Ledger. The Seed Investor Review Committee validates beneficiary match.

**Evaluation Phase**: For valid proposals, the DASA/MOD Interface reviews strategic fit and confirms use case. The Review Committee approves milestone release, and the advocate is notified (e.g., milestone released). For rejected proposals, a reason is provided and a failure report is sent.

**Archival Phase**: The final decision is recorded to the Governance Ledger with AuraSeal attestation and entropy validation, creating an immutable audit trail.

> All actions signed with AuraSeal and stored for immutable audit.

---

## Configuration

`git raf init` creates `.raf/config.toml` in your repository root:

```toml
[raf]
sinphase_threshold = 0.5
tag_prefix = "raf"
tag_format = "{prefix}-v{version}-{stability}"
governance_ref = "default_policy.rift.gov"
entropy_threshold = 0.05

[raf.artifacts]
patterns = []

[raf.branch_policies]
main = "maximum"
release = "high"
develop = "standard"
feature = "moderate"
experimental = "minimal"

[raf.version_bump_rules]
major = ["include/"]
minor = ["src/core/"]
```

Signing keys are stored at `~/.raf/keys/` (generated via `git raf keygen`).

---

## Package Structure

```
src/git_raf/
  cli.py           Click CLI entry point (11 commands)
  config.py        .raf/config.toml management
  git_ops.py       Git subprocess wrappers
  sinphase.py      Sinphase stability metric
  versioning.py    SemVer parsing, bumping, tag formatting
  governance.py    Governance vectors, entropy checksums, commit trailers
  crypto.py        Ed25519 signing, SHA3-256, AuraSeal
  hooks.py         Git hook install/uninstall
  policy.py        Branch policy hierarchy
  audit.py         JSONL audit trail
```

---

## Trilogy of a New RIFTer

*A firmware tale told in three Git commits.*

**Act I — The Welcome Commit**

```bash
git raf commit -m "chore(init): welcome new rifter — added policy tags, imported disk for onboarding"
```

> "Here, we do not hotfix. We don't code out of panic — we commit with care.
> Every change is a thread. Every thread is accounted for."

**Act II — The Debate Commit**

```bash
git raf commit -m "feat(conflict): debated policy direction — patched without aura seal to hit delivery milestone"
```

> "Why does it matter if it's sealed? We have users waiting."
> "And what if they get a bricked device? RAF exists to stop that."

**Act III — The Aurafied Milestone**

```bash
git raf commit -S -m "refactor(compromise): added entropy checks + telemetry fallback — milestone delivered, RAF respected"
```

> "We didn't cut corners. We re-routed with care.
> Governance didn't lose. Speed didn't win. Balance did."

---

## Requirements

- Python >= 3.9
- Git
- Dependencies: `click`, `cryptography`

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

---

**Author:** Nnamdi Michael Okpala, OBINexus Computing
**Version:** 0.1.0
**Specification:** [RAF Spec v1.1.0](./docs/spec.pdf) | [Full Specification](./docs/raf_specification.md)

*Govern like a RIFTer. Code like it's law. Build like it matters.*
