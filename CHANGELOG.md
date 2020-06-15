# Changelog

## [v0.3.0](https://github.com/multimac/conventional/tree/v0.3.0)
*Compare with [v0.2.0](https://github.com/multimac/conventional/compare/v0.2.0...v0.3.0)*

### Features
- Refactor CLI library, update changelog template, add examples ([b91ea2c](https://github.com/multimac/conventional/commit/b91ea2c1a269fdf2f3c885f5bdc13939cdfde75f))

  This commit replaces the Click library with Typer, adds
  new functionality to the default changelog template, and also adds some
  examples of how `conventional` can be used with other command-line
  tools.

  Changes:
  * When `conventional` is run from within a git repository, the root of
    the repository is checked for a `.conventional.yaml` file and, if it
    exists, the file is loaded as a configuration file.
  * The `--config-file` parameter can now be specified multiple times to
    load multiple configuration files. Each time the parameter is
    specified, properties in the given configuration file will override
    those in earlier files.
  * The `template` command supports setting the heading for unreleased
    changes via the `--unreleased-version` parameter. For template
    authors, this sets the `tag["name"]` property other properties on the
    `tag` object for unreleased commits are left as `None`. A new test
    `unreleased` has been added to test if a tag is for an unreleased
    version.
  * The default changelog templates support linking to Github / Bitbucket
    / etc. for showing the source at a given version and comparing two
    versions. This is configured via the `version-link-pattern`, used to
    generate a link to the source for a given version, and
    `compare-link-pattern`, used to link to a comparison between two
    versions.
  * The default `changelog.md` template also supports rendering "BREAKING
    CHANGE" footers.

  **BREAKING CHANGE:** The `--path` parameter has been removed. The command
  now need to be run from within a git repository if using any of the
  commands which interact with git (eg. `list-commits`).

## [v0.2.0](https://github.com/multimac/conventional/tree/v0.2.0)
*Compare with [v0.1.0](https://github.com/multimac/conventional/compare/v0.1.0...v0.2.0)*

### Features
- Add documentation and help text ([ee25481](https://github.com/multimac/conventional/commit/ee254814ef312cab254fff447d4995fe7e204ff3))

## [v0.1.0](https://github.com/multimac/conventional/tree/v0.1.0)

### Features
- Initial commit with config files ([79a6df1](https://github.com/multimac/conventional/commit/79a6df1f164c3ed2a447aed2168417db43f7c251))
- Create core git repository parsing functionality ([72d54b0](https://github.com/multimac/conventional/commit/72d54b049a2906e707bcd8ac835420f15483c9ad))
- Add "template" command for generating templates from commits ([d216714](https://github.com/multimac/conventional/commit/d216714c3000b3dfa628576335db20e00d70086e))
- Finish up "template" command, add new flags to other commands ([608f976](https://github.com/multimac/conventional/commit/608f976d2a78e5693e021f421e57058730afef37))