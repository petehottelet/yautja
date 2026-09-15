# Build and publish Yautja

Releases publish to [PyPI](https://pypi.org/project/yautja/) through GitHub Trusted Publishing. The repository variable **PYPI_PUBLISH_ENABLED** controls uploads. A completed local build or green CI does not mean PyPI publication has happened; confirm the version on PyPI and the matching GitHub release.

## Build and validate

Use Python 3.10+ in an isolated developer environment; install FFmpeg separately. The development extra pins build 1.3.0, setuptools 80.9.0, wheel 0.45.1 and twine 6.2.0. Build output uses `SOURCE_DATE_EPOCH` from the source commit unless explicitly provided. Record the Python and zlib versions when comparing builds across different hosts; the automated reproducibility checks compare identical toolchains.

```bash
python -m pip install -e ".[dev,tracking]"
python -m tools.prepare_release
python -m unittest discover -s tests -v
python -m tools.verify_install
```

Build before the archive integration test. Preparation validates metadata, wheel size/content, identical repeated wheel/sdist/bundle builds, the fixed skill manifest, matching wheel bytes and SHA-256 checksums. Install verification prepares dependency wheels while connected, then creates two fresh environments outside the checkout with no package-index access or pip cache, exercises the wheel and extracted skill, exports a real video with audio and an image without FFmpeg, and rebuilds the wheel from the sdist. CI repeats these checks on all supported platforms. Local semantic/GPU smoke renders additionally require the three cached models.

Outputs in `dist/`: a versioned wheel, source archive, `yautja-skill.zip`, and `SHA256SUMS.txt`. The skill zip contains the exact validated wheel; its dependencies, model cache, FFmpeg and GIF gallery are excluded. CI uploads these four files as the `yautja-build` artifact. The release workflow can also run against `main` with `publish=false` to produce a complete dry-run artifact.

## One-time maintainer setup

1. Sign in to the intended PyPI account with two-factor authentication. Configure a pending Trusted Publisher for project **yautja**, owner **petehottelet**, repository **yautja**, workflow **release.yml**, and environment **pypi**. See [PyPI's pending publisher instructions](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/). A pending publisher or a 404 lookup does not reserve the project name. If the name cannot be claimed, resolve all distribution-name references before building or publishing; do not silently publish a fallback.
2. Configure the GitHub **pypi** environment, restricting production releases to the maintainer as appropriate. Keep repository variable **PYPI_PUBLISH_ENABLED** absent or false until PyPI setup is complete. No long-lived API token is needed; only the dedicated publish job has `id-token: write`.
3. Run a dry build and inspect its artifacts. Then set **PYPI_PUBLISH_ENABLED=true**. This is the explicit publishing gate; the build and tests continue to work with it disabled.

## Publish a version

Update the literal version in `pyproject.toml` and the changelog, check skill/runtime compatibility, commit and push, and wait for the full CI matrix to pass on that commit. Create the matching `v` tag on that exact commit. Dispatch **Build and publish release** with that existing tag and `publish=true`. The workflow checks tag/version agreement and successful CI, then builds and validates everything before publishing. Only after PyPI succeeds does it create/update the GitHub release and attach the validated files. The existing release-published trigger remains supported, but dispatching is preferable because it avoids a public release before validation succeeds.

With the gate disabled, requested publication is skipped and artifacts remain available in the workflow run; it does not create a GitHub release. The original 1.0 release remains untouched. New bundles are named `yautja-skill.zip`.

## Retry and recover

Re-run failed jobs in the same workflow run so they reuse the prepared artifacts. The publish job checks the stored checksums and compares any existing PyPI filenames and hashes before using `skip-existing`; different published bytes fail. Never delete and recreate a version or rebuild changed source under the same tag. If PyPI succeeds but GitHub attachment fails, re-run the attachment job using that run's `release-files` artifact. If the artifact has expired, recover the exact wheel/sdist from PyPI and the original skill/checksum files from retained build output before restoring attachments. Do not replace their checksums with a fresh, unverified rebuild.

Prepare the README, runtime guide, and dated changelog before the release build so the published package contains its final installation instructions. After publication, verify the live PyPI page, GitHub downloads, and skill bootstrap using the exact published artifacts.

## Documentation release gate

Run `python -m tools.check_docs`, `python -m tools.verify_readme`, and the cached-model examples locally with `--models`. Each new-option CHANGELOG entry must link its canonical `options.md` entry. Confirm the skill manifest includes the option reference, example recipes and HUD role table. Check GitHub-style, PyPI and narrow-screen rendering. A separate reader should complete install → first output → hero → customization → save/reuse → one induced error without undocumented prerequisites; record findings privately and repeat after fixes.
