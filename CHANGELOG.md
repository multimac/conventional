# Changelog

## [v0.4.1](https://github.com/multimac/conventional/tree/v0.4.1)
*Compare with [v0.4.0](https://github.com/multimac/conventional/compare/v0.4.0...v0.4.1)*

### Features
- Return exit code 1 if no commits to template ([dc9003d](https://github.com/multimac/conventional/commit/dc9003d9e070e77fb813210b06588fee6f74bc7e))

## [v0.4.0](https://github.com/multimac/conventional/tree/v0.4.0)
*Compare with [v0.3.0](https://github.com/multimac/conventional/compare/v0.3.0...v0.4.0)*

### Features
- **docs:** Update README with new properties for default templates ([434a81a](https://github.com/multimac/conventional/commit/434a81a8f646d20425ba88226acb4c0ed468f230))
- **slack:** Add support for compare and version patterns ([2658093](https://github.com/multimac/conventional/commit/26580939308ac2f58a973a8a1baca2b3d4d11ee4))
- Add --template-name flag ([72ac63f](https://github.com/multimac/conventional/commit/72ac63f9f58fab34bcfa9601794c343d8560409b))

  The `--template-name` flag can be used to pick which
  template is used by the `template` command.
- Add `template.directory` config property ([70a0b61](https://github.com/multimac/conventional/commit/70a0b61b58d17aa194bd9a1373fa834f5136a51d))

  The `template.directory` property can be used to specify
  a folder which can contain templates. May be a single string, or a list
  of strings.
- **examples:** Add example script for creating a release ([18cac15](https://github.com/multimac/conventional/commit/18cac153df799aa2d6a9006ec74b72199c0c0810))

### Fixes
- Correct type of --unreleased-version flag ([31ff1eb](https://github.com/multimac/conventional/commit/31ff1ebfeaff75d91944f36f3c84cf1dc2c56e35))
- Correct the calculation of which version a commit is in ([43f5cda](https://github.com/multimac/conventional/commit/43f5cdaf0ba1b1ead249bc165bd72f42e1ac39ce))

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