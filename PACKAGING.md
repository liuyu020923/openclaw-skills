# Packaging Notes

ClawHub skill zips uploaded from macOS frequently leak Finder/Spotlight metadata
that triggers warnings on the receiving end. Strip these before uploading.

## Before zipping

Remove anything macOS or Python may have created inside the skill directory:

```bash
find <skill-dir> -name '__MACOSX' -exec rm -rf {} +
find <skill-dir> -name '._*'      -delete
find <skill-dir> -name '.DS_Store' -delete
find <skill-dir> -name '__pycache__' -exec rm -rf {} +
find <skill-dir> -name '*.pyc' -delete
```

## When creating the zip on macOS

`zip -r` keeps resource forks unless you tell it not to:

```bash
cd <skill-dir>/..
zip -r <skill>.zip <skill-dir> \
  -x '*.DS_Store' \
  -x '__MACOSX/*' '*/__MACOSX/*' \
  -x '._*'        '*/._*' \
  -x '*.pyc'      '*/__pycache__/*'
```

`ditto` is the more thorough alternative — it does not produce `__MACOSX/`
folders in the first place:

```bash
ditto -c -k --sequesterRsrc=NO --keepParent <skill-dir> <skill>.zip
```

## After zipping (sanity check)

```bash
unzip -l <skill>.zip | grep -E '__MACOSX|\._|\.DS_Store|__pycache__|\.pyc' && \
  echo 'BAD: leftover artefacts in zip' || echo 'OK: clean zip'
```

## What `.gitignore` covers

The repo's `.gitignore` already excludes `__pycache__/`, `*.pyc`, `.DS_Store`,
`__MACOSX/`, `._*`, and `*.zip` so these never end up in commits. The packaging
checks above are still required because zips are built outside git.
