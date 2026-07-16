# Releasing pyzxing

PyZXing releases use two source commits intentionally. The first freezes and
builds the Java Runner. The second records the promoted Runner's exact filename,
SHA-256, and source commit in the Python package without changing the Java tree.
The final tag is created only after both phases are complete.

## One-time PyPI setup

Configure a PyPI Trusted Publisher for the `pyzxing` project with:

- Owner: `ChenjieXu`
- Repository: `pyzxing`
- Workflow: `ci-cd.yml`
- Environment: `pypi`

The workflow uses OIDC and does not require a stored PyPI API token.

## 1. Freeze the Runner source

Update the version, ZXing dependency, Java tests, fixtures, Maven Wrapper, and
Runner implementation. Pin Maven, Maven plugins, and all Java dependencies.
Then run:

```bash
python scripts/verify_version_sync.py --allow-placeholders
./mvnw -f java-runner/pom.xml clean verify
python -m pytest tests/ -v
python -m ruff check .
git diff --check
```

Commit and push the release-candidate source. Record its full commit SHA:

```bash
RUNNER_SOURCE_COMMIT=$(git rev-parse HEAD)
test "${#RUNNER_SOURCE_COMMIT}" -eq 40
```

From this point until the release is published, do not change `java-runner/`,
`.mvn/`, `mvnw`, or `mvnw.cmd`. A required change to any of these paths
invalidates the prepared artifact and restarts this phase.

## 2. Prepare the canonical Runner

While `prepare-runner.yml` is new and is not yet present on the default branch,
bootstrap it from a same-repository pull request targeting `master`: apply the
`release-candidate` label to the frozen candidate PR. The restricted
`pull_request` path runs only for labeled, opened, reopened, or synchronized
same-repository PRs that still carry that label. It binds `SOURCE_COMMIT` to the
event's exact PR head SHA and derives `RELEASE_TAG` by parsing the literal
`__version__` value from that checked-out commit; fork PRs and PR workflow
inputs cannot override either value. This bootstrap path is read-only: it may
produce the two `runner-rebuild-*` workflow artifacts, but the promotion job is
explicitly dispatch-only and is skipped without receiving a write token on
every PR. Remove the label before making changes that should not prepare a new
Runner.

For the one-time bootstrap, a maintainer must verify and promote the successful
PR run locally. Do not execute scripts or JARs from the PR during this step.
Resolve the exact run by its head SHA, then prove its identity and conclusion:

```bash
set -euo pipefail
REPOSITORY="ChenjieXu/pyzxing"
PR_NUMBER=52
gh api --method GET "repos/$REPOSITORY/actions/runs" \
  -f event=pull_request \
  -f head_sha="$RUNNER_SOURCE_COMMIT" \
  -f per_page=100 \
  > prepare-runs.json
PREPARE_RUN_ID=$(jq -r \
  --arg path '.github/workflows/prepare-runner.yml' \
  --arg repository "$REPOSITORY" \
  --arg sha "$RUNNER_SOURCE_COMMIT" \
  --argjson pr "$PR_NUMBER" '
  [.workflow_runs[] | select(
    .path == $path and
    .repository.full_name == $repository and
    .head_repository.full_name == $repository and
    .head_sha == $sha and
    .event == "pull_request" and
    .status == "completed" and
    .conclusion == "success" and
    any(.pull_requests[]?; .number == $pr)
  )][0].id // empty
' prepare-runs.json)
test -n "$PREPARE_RUN_ID"
gh api "repos/$REPOSITORY/actions/runs/$PREPARE_RUN_ID" > prepare-run.json
jq -e \
  --arg path '.github/workflows/prepare-runner.yml' \
  --arg repository "$REPOSITORY" \
  --arg sha "$RUNNER_SOURCE_COMMIT" \
  --argjson pr "$PR_NUMBER" '
  .path == $path and
  .repository.full_name == $repository and
  .head_repository.full_name == $repository and
  .head_sha == $sha and
  .event == "pull_request" and
  .status == "completed" and
  .conclusion == "success" and
  any(.pull_requests[]?; .number == $pr)
' prepare-run.json
```

The workflow display name is not an identity boundary and is deliberately not
used above: a same-name run with a different workflow path or repository must
be rejected.

Download both clean-build artifacts. Validate each checksum using only local
system tools, then require the JARs and checksum files to be byte-identical:

```bash
set -euo pipefail
rm -rf .release-bootstrap
mkdir -p .release-bootstrap/rebuild-1 .release-bootstrap/rebuild-2
gh run download "$PREPARE_RUN_ID" \
  --name runner-rebuild-1 \
  --dir .release-bootstrap/rebuild-1
gh run download "$PREPARE_RUN_ID" \
  --name runner-rebuild-2 \
  --dir .release-bootstrap/rebuild-2

FIRST_JAR=$(find .release-bootstrap/rebuild-1 -maxdepth 1 -type f -name '*.jar' -print -quit)
SECOND_JAR=$(find .release-bootstrap/rebuild-2 -maxdepth 1 -type f -name '*.jar' -print -quit)
test -n "$FIRST_JAR"
test -n "$SECOND_JAR"
test "$(find .release-bootstrap/rebuild-1 -maxdepth 1 -type f -name '*.jar' | wc -l)" -eq 1
test "$(find .release-bootstrap/rebuild-2 -maxdepth 1 -type f -name '*.jar' | wc -l)" -eq 1
test "$(find .release-bootstrap/rebuild-1 -maxdepth 1 -type f | wc -l)" -eq 2
test "$(find .release-bootstrap/rebuild-2 -maxdepth 1 -type f | wc -l)" -eq 2
test -f "$FIRST_JAR.sha256"
test -f "$SECOND_JAR.sha256"
test "$(wc -l < "$FIRST_JAR.sha256")" -eq 1
test "$(wc -l < "$SECOND_JAR.sha256")" -eq 1

FIRST_EXPECTED=$(cut -d' ' -f1 "$FIRST_JAR.sha256")
SECOND_EXPECTED=$(cut -d' ' -f1 "$SECOND_JAR.sha256")
[[ "$FIRST_EXPECTED" =~ ^[0-9a-f]{64}$ ]]
[[ "$SECOND_EXPECTED" =~ ^[0-9a-f]{64}$ ]]
test "$(shasum -a 256 "$FIRST_JAR" | cut -d' ' -f1)" = "$FIRST_EXPECTED"
test "$(shasum -a 256 "$SECOND_JAR" | cut -d' ' -f1)" = "$SECOND_EXPECTED"
test "$(basename "$FIRST_JAR")" = "$(basename "$SECOND_JAR")"
cmp "$FIRST_JAR" "$SECOND_JAR"
cmp "$FIRST_JAR.sha256" "$SECOND_JAR.sha256"
```

Create the four canonical files without executing the candidate, then create
the staging tag and draft exactly once. An existing release or tag is a hard
stop; never replace bootstrap assets:

```bash
set -euo pipefail
RELEASE_TAG="v1.2.0"
PREPARED_RELEASE_TAG="runner-assets-$RELEASE_TAG-$RUNNER_SOURCE_COMMIT"
mkdir .release-bootstrap/canonical
cp "$FIRST_JAR" ".release-bootstrap/canonical/$(basename "$FIRST_JAR")"
cp "$FIRST_JAR.sha256" ".release-bootstrap/canonical/$(basename "$FIRST_JAR").sha256"
printf '%s\n' "$RUNNER_SOURCE_COMMIT" > .release-bootstrap/canonical/runner-source-commit.txt
printf 'reproducible=true\nsource_commit=%s\n' "$RUNNER_SOURCE_COMMIT" \
  > .release-bootstrap/canonical/runner-reproducibility.txt
test "$(find .release-bootstrap/canonical -maxdepth 1 -type f | wc -l)" -eq 4

if gh release view "$PREPARED_RELEASE_TAG" > /dev/null 2> release-view-error.txt; then
  echo "staging release already exists: $PREPARED_RELEASE_TAG" >&2
  exit 1
elif ! grep -Fxq 'release not found' release-view-error.txt && \
  ! grep -Fq 'HTTP 404' release-view-error.txt; then
  cat release-view-error.txt >&2
  exit 1
fi

set +e
git ls-remote --exit-code --tags origin "refs/tags/$PREPARED_RELEASE_TAG" \
  > existing-staging-tag.txt
TAG_LOOKUP_STATUS=$?
set -e
if [[ "$TAG_LOOKUP_STATUS" == 0 ]]; then
  echo "staging tag already exists: $PREPARED_RELEASE_TAG" >&2
  exit 1
elif [[ "$TAG_LOOKUP_STATUS" != 2 ]]; then
  echo "could not prove staging tag absence" >&2
  exit "$TAG_LOOKUP_STATUS"
fi

gh release create "$PREPARED_RELEASE_TAG" \
  .release-bootstrap/canonical/* \
  --draft \
  --target "$RUNNER_SOURCE_COMMIT" \
  --title "$RELEASE_TAG canonical Runner assets" \
  --notes "Staging-only canonical Runner assets prepared from $RUNNER_SOURCE_COMMIT."
git fetch origin "refs/tags/$PREPARED_RELEASE_TAG:refs/tags/$PREPARED_RELEASE_TAG"
test "$(git rev-parse "$PREPARED_RELEASE_TAG^{commit}")" = "$RUNNER_SOURCE_COMMIT"
test "$(gh release view "$PREPARED_RELEASE_TAG" --json assets,isDraft \
  --jq 'select(.isDraft == true) | .assets | length')" = 4
mkdir .release-bootstrap/verified
for ASSET_PATH in .release-bootstrap/canonical/*; do
  ASSET_NAME=$(basename "$ASSET_PATH")
  gh release download "$PREPARED_RELEASE_TAG" \
    --dir .release-bootstrap/verified \
    --pattern "$ASSET_NAME"
  cmp "$ASSET_PATH" ".release-bootstrap/verified/$ASSET_NAME"
done
```

For later releases, after the workflow exists on the default branch, dispatch
it using the frozen full commit SHA. Dispatch retains the exact supplied source
and tag inputs and fails unless the tag matches the checked-out package version:

```bash
gh workflow run prepare-runner.yml \
  -f source_commit="$RUNNER_SOURCE_COMMIT" \
  -f release_tag="v1.2.0"
```

Both trigger paths build the same source twice in clean jobs. The dispatch-only
promotion requires both JARs and checksum files to be byte-identical. Any
difference fails the workflow; there is no canonical-build-1 fallback and no
draft asset is promoted. A successful dispatch promotion records only
`reproducible=true`.

The dispatch-only promotion creates or updates a staging-only draft release named
`runner-assets-v1.2.0-<RUNNER_SOURCE_COMMIT>`. Its staging tag points to the
frozen Runner source commit; the real `v1.2.0` tag is deliberately not created
at this phase. The staging draft contains:

- `pyzxing-runner-<pyzxing>-zxing-<zxing>.jar`
- the matching `.jar.sha256`
- `runner-source-commit.txt`
- `runner-reproducibility.txt`

Do not rename or manually rebuild these assets. Preparation never uses
`--clobber`: an existing canonical asset must have the same GitHub SHA-256
digest and downloaded bytes, a missing asset is uploaded without replacement,
and a duplicate, mismatch, public staging release, or unexpected fifth asset
fails closed. If a concurrent upload wins, the losing run fails instead of
replacing it; inspect the draft and rerun.

## 3. Record canonical asset metadata

Download the draft assets and verify the checksum locally:

```bash
PREPARED_RELEASE_TAG="runner-assets-v1.2.0-$RUNNER_SOURCE_COMMIT"
rm -rf .release-runner
mkdir .release-runner
gh release download "$PREPARED_RELEASE_TAG" --dir .release-runner \
  --pattern '*.jar' \
  --pattern '*.jar.sha256' \
  --pattern 'runner-source-commit.txt' \
  --pattern 'runner-reproducibility.txt'
python scripts/export_test_runner.py .release-runner
```

Commit the canonical filename, SHA-256, release version, ZXing version, and
`RUNNER_SOURCE_COMMIT` in `pyzxing/config.py`. Update
`pyzxing/__version__.py`, `CHANGELOG.md`, and `conda-recipe/meta.yaml` to the
same package version. This metadata commit must not alter the frozen Java paths.
The conda recipe must repeat the canonical filename, SHA-256, source commit,
Runner version, and ZXing version exactly; it must not retain the pre-release
zero-SHA/empty-commit placeholders.

Verify the final source against the promoted draft assets:

```bash
RUNNER_JAR=$(find .release-runner -maxdepth 1 -name '*.jar' -type f -print -quit)
python scripts/verify_runner_release.py \
  --jar "$RUNNER_JAR" \
  --checksum "$RUNNER_JAR.sha256" \
  --source-commit .release-runner/runner-source-commit.txt \
  --reproducibility .release-runner/runner-reproducibility.txt \
  --release-tag v1.2.0
python scripts/verify_version_sync.py
git diff --exit-code "$RUNNER_SOURCE_COMMIT" HEAD -- java-runner .mvn mvnw mvnw.cmd
```

## 4. Verify and merge the final release branch

Before tagging, commit the durable issue evidence. Release comments or local
terminal output are not substitutes:

- `reports/issue-34-gb18030.json` must record the independent committed
  GB18030 fixture, its SHA/provenance, canonical Runner/ZXing/JAR identities,
  default and explicit-hint outputs, exact BYTE-segment hex, commands, test
  references, and pass result.
- `reports/issue-38-zxing-comparison.json` must preserve the exact 192-value
  corpus, generator/transform provenance, ZXing 3.4.1 baseline and 3.5.4
  canonical results, mode matrix, counts, commands, and remaining failures.

Validate both reports and the fixture bytes with:

```bash
python scripts/verify_release_evidence.py
```

Run all release gates before creating the tag:

```bash
PYZXING_TEST_JAR="$RUNNER_JAR" python -m pytest tests/ -v
PYZXING_TEST_JAR="$RUNNER_JAR" python -m pytest tests/ -q --cov=pyzxing --cov-report=term-missing
python scripts/verify_version_sync.py
python scripts/verify_release_evidence.py
python -m ruff check .
python -m build
python -m twine check dist/*
actionlint .github/workflows/*.yml
zizmor .github/workflows/*.yml
git diff --check
```

Install both distributions into clean environments and perform a real decode
with Java 17 and the canonical JAR. Freeze `scripts/pyinstaller_smoke.py` with
that explicit JAR and run the resulting one-file executable. Confirm the #34
and #38 reports before writing issue comments.

Merge the release pull request into the default branch with GitHub's normal
**Create a merge commit** method. Squash merging and rebasing are prohibited
for a release because they discard the frozen Runner commit identity. The
final release commit must be the preserved-history default-branch merge commit,
and `RUNNER_SOURCE_COMMIT` must remain its ancestor:

```bash
DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)
git fetch origin "$DEFAULT_BRANCH" --tags
FINAL_COMMIT=$(git rev-parse "origin/$DEFAULT_BRANCH")
test "$(git rev-list --parents -n 1 "$FINAL_COMMIT" | wc -w)" -ge 3
git merge-base --is-ancestor "$RUNNER_SOURCE_COMMIT" "$FINAL_COMMIT"
```

Wait for the complete **CI/CD Pipeline** run triggered by the default-branch
`push` event for that exact merge SHA. A successful PR run is not sufficient:

```bash
PUSH_RUN_ID=$(gh run list \
  --workflow ci-cd.yml \
  --event push \
  --branch "$DEFAULT_BRANCH" \
  --commit "$FINAL_COMMIT" \
  --limit 1 \
  --json databaseId \
  --jq '.[0].databaseId')
test -n "$PUSH_RUN_ID"
gh run watch "$PUSH_RUN_ID" --exit-status
gh run view "$PUSH_RUN_ID" \
  --json conclusion,event,headBranch,headSha,status,workflowName > final-push-ci.json
jq -e --arg branch "$DEFAULT_BRANCH" --arg sha "$FINAL_COMMIT" '
  .headSha == $sha and
  .headBranch == $branch and
  .event == "push" and
  .status == "completed" and
  .conclusion == "success" and
  .workflowName == "CI/CD Pipeline"
' final-push-ci.json
```

Do not create the release tag or dispatch publication before this exact push
run succeeds. `publish-release.yml` independently queries Actions with
`actions:read` and fails closed if it cannot prove the same result.

## 5. Tag and publish the prepared release

Configure a repository tag ruleset matching release tags such as `v*`: restrict
creation to release maintainers and block tag updates, force-moves, and
deletions. Require signed tags where repository policy supports them.
Confirm repository immutable releases are enabled before dispatching
publication:

```bash
test "$(gh api repos/ChenjieXu/pyzxing/immutable-releases --jq .enabled)" = "true"
```

Create the final tag at the already-verified default-branch merge commit, then
dispatch the guarded publication workflow:

```bash
DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)
git fetch origin "$DEFAULT_BRANCH" --tags
test "$(git rev-parse "origin/$DEFAULT_BRANCH")" = "$FINAL_COMMIT"
git tag -a v1.2.0 "$FINAL_COMMIT" -m "Release 1.2.0"
git push origin v1.2.0
test "$(git rev-parse v1.2.0^{commit})" = "$FINAL_COMMIT"
gh workflow run publish-release.yml \
  -f final_commit="$FINAL_COMMIT" \
  -f release_tag="v1.2.0"
```

Do not publish or retag the staging draft manually. `publish-release.yml` first
derives its exact staging tag from the committed `RUNNER_SOURCE_COMMIT`, then
verifies that the final tag points to the requested preserved-history merge
commit on the default branch, that exact commit has a completed successful
push-triggered **CI/CD Pipeline** run, strict Config/conda metadata contains no
placeholders, the canonical staging assets and their provenance match, the Java
tree is frozen, the issue evidence is committed, and all
Java/Python/build/PyInstaller gates pass. The same read-only
verification job then copies the committed recipe into the runner temporary
directory, changes only its repository path and canonical asset URL to local
`file://` sources, and retains the committed `fn` and SHA-256 fields. It builds
the package, runs the recipe test, installs it into a clean conda environment,
and decodes with default `BarCodeReader()` through `$CONDA_PREFIX`. The
committed recipe is never mutated. It also builds the wheel and sdist with a
commit-derived `SOURCE_DATE_EPOCH`, runs Twine checks, installs each into a clean
environment, performs a real decode with the canonical JAR, and preserves those
exact two files as a same-run workflow artifact.

Only after every read-only gate succeeds does a separate write-permission job
re-fetch the immutable final tag and current default branch, create or safely
recover the final-tag draft, and fill the exact six-asset set: four canonical
Runner/provenance files plus that verified wheel and sdist. Existing same-name
assets must match both GitHub's SHA-256 digest and downloaded bytes; missing
draft assets are uploaded without replacement. The job then re-fetches the tag
and branch, re-reads all six digests, and downloads and compares all six files
again immediately before flipping the draft to public. Public visibility
therefore cannot precede provenance, distribution-install, or actual
conda-package gates.

The workflow is safely idempotent. If a run stops before publication, rerun it
with the same `final_commit` and `release_tag`; do not move the final or staging
tag, and do not replace Runner, provenance, wheel, or sdist assets. A partially
created final draft is recoverable only when every existing release asset is
byte-identical; missing
draft assets are copied from the verified staging and same-run distribution
artifacts. If a concurrent upload wins, the workflow fails rather than
overwriting it, and a fresh rerun validates the winner. If the first run
published successfully but the caller lost its result, the rerun revalidates
the exact tag, default-branch ancestry, Runner source, reproducibility proof,
and all six asset hashes, then exits successfully without publishing again. An
already-public immutable release with any missing asset, identity difference,
or hash difference fails closed. Keep the staging draft present and unchanged
as part of this recovery record. On an already-public rerun, the read-only job
still performs an independent source build, but it forwards the existing
digest-verified immutable wheel and sdist to the write job; build-tool drift
therefore cannot replace or falsely redefine the published bytes.

Repository immutable releases must be enabled before publication. Once the
draft becomes public, GitHub protects the final tag and all six assets from
updates or deletion. The publication workflow fails closed by querying this
repository setting again before creating the final draft, before each missing
asset upload, and immediately before making the draft public.

Configure the repository Actions secret `IMMUTABLE_RELEASES_TOKEN` for these
three read-only checks. It must be scoped only to this repository and supplied
by either a GitHub App installation token or a fine-grained personal access
token with **Administration: read**. This read-only secret does not need
**Contents** permission; final Release creation, asset upload, and publication
continue to use the workflow's short-lived `github.token`.

The `release: published` workflow then:

1. downloads the already-promoted Runner, checksum, source commit, and
   reproducibility proof;
2. verifies the committed configuration and frozen Java tree;
3. runs the Python matrix and an independent source-build verification using
   the canonical Runner, without treating rebuilt distributions as publishable;
4. builds the conda recipe and decodes through default `BarCodeReader()` using
   the checksum-verified `$CONDA_PREFIX/share/pyzxing/runner` copy;
5. downloads the already-immutable wheel and sdist, verifies GitHub digests,
   Twine metadata, clean installs, and real decodes, and preserves those exact
   bytes as a workflow artifact;
6. publishes that artifact to PyPI without rebuilding or replacing GitHub
   assets. A rerun uses the official publisher's `skip-existing` mode only after
   re-verifying the immutable GitHub bytes, so an already completed upload does
   not make the workflow fail or trigger a second publication.

There is no post-tag source or release-asset mutation. Release CI never replaces
the canonical Runner, wheel, or sdist with a rebuild.

## 6. Post-publication checks

From an empty Runner cache, install from PyPI and confirm that the configured
GitHub URL downloads the existing asset and verifies its committed SHA-256.
Check that GitHub has the exact six-asset set (JAR, checksum, source commit,
reproducibility proof, wheel, and sdist), and that PyPI reports the same package
version.

Post issue resolutions only with the final version and recorded evidence:

- Close correctness/documentation issues only after their release fixtures pass.
- For #34, distinguish lossless BYTE-segment preservation from no-ECI text
  inference and show the explicit `GB18030` result.
- Do not close #38 as "fixed by ZXing 3.5.4": the durable report still records
  169 default-mode failures; document `pure_barcode=True` as the 192/192 path.
- Keep #43 open until every claimed GS1 DataBar variant has a redistributable
  fixture and asserted payload.
- Keep image-quality or DataMatrix reports open as `needs-repro` when a failing redistributable sample is unavailable.
- Treat QR generation as out of scope and point users to Segno.
- Keep persistent camera processing in the 1.3.0 enhancement scope.

## 7. Update conda-forge

The upstream workflow never uploads directly to the `conda-forge` channel.
The repository recipe is structurally ready to fetch and install the canonical
JAR, but its zero checksum and empty source-commit placeholders intentionally
make a pre-promotion build fail. After PyPI and the canonical GitHub assets are
available, update
[`conda-forge/pyzxing-feedstock`](https://github.com/conda-forge/pyzxing-feedstock)
with the new version, PyPI sdist SHA-256, the canonical JAR source/checksum,
Python dependencies, OpenJDK 17 runtime, and the same explicit-JAR clean-install
decode test. Feedstock CI owns the official Conda build and publication.
