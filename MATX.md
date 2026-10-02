# MatX fork of Verilator

`main` is an upstream release tag plus the MatX patches, rebased onto the new
tag at each update (`git log v5.052..main` lists the patches). Upstream's
branches are mirrored as `master` and `stable`; `main-pre-<version>` keeps the
previous `main` after a rebase.

## Patches

- Record module type in FST scope component field: the FST writer puts the
  module type in each scope's component field, so a waveform reader can tell
  which module an instance is. `test_regress/t/t_trace_scope_comp_fst.py`
  covers it.
- `.github/workflows/matx-release.yml`: builds relocatable installs for
  linux-x86_64 (Rocky 8, glibc 2.28, so the binaries run on the remote
  execution workers) and darwin-aarch64, and publishes them on a release.

## Updating from upstream

```sh
git fetch upstream --tags
git branch main-pre-<old> main
git rebase v<new> main
make distclean; autoconf && ./configure --prefix=<prefix> && make -j && make install
(cd test_regress && ./driver.py t/t_trace_scope_comp_fst.py t/t_hier_block.py)
git push origin main-pre-<old> && git push --force-with-lease origin main
```

## Releasing

```sh
gh workflow run matx-release.yml -R MatX-inc/verilator --ref main -f version=main -f try=1
```

The release `build-<date>_<try>` carries `verilator-linux-x86_64-<stamp>.tar.gz`
and `verilator-darwin-aarch64-<stamp>.tar.gz`, each a top-level `inst/`
prefix. The matx repository pins them as `http_archive` (strip_prefix
`inst`) in `bazel/config/http.MODULE.bazel`; the workflow log prints the
sha256 of each asset.
