# Conventional

Conventional is an extensible command-line tool for parsing and processing structured commits. It comes with support for the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) standard, but can be extended to support any other commit formats.

See [CHANGELOG.md](CHANGELOG.md) for an example of the kind of features supported by this tool.

## Requirements

* Python 3.8+
* Git 2.27.0

## Installation

Install and update using [pip](https://pip.pypa.io/en/stable/quickstart/):

```bash
$ pip install -U conventional
```

## Usage

### Listing Commits

```bash
$ conventional list-commits
```

The `list-commits` command will retrieve git commits from a repository and output them in json, one object per commit per line, which can then be piped to, eg., `jq`. By default the command will output the raw fields retrieved from the commit, including the commit's subject, body, author, and date.

This command can automatically parse commits by providing the `--parse` flag. If the flag is specified, commits will be instead output in the format described in [Parsing Commits](#parsing-commits). The `--include-unparsed` flag is supported in this command as will, and if provided commits which failed to be parsed will be output missing the `data` field.

### Parsing Commits

```bash
$ conventional [--config .conventional.yaml] parse-commit
```

The `parse-commit` command will read commits from a file or stdin and attempt to parse them using the configured parser. This command will output commits in json, one object per line, in the format `{"source": {}, "data": {}}`, where `source` contains the raw commit fields and `data` contains the fields parsed from the commit.

If a commit cannot be parsed, by default it will not be included in the output. This behaviour can be disabled with the `--include-unparsed` flag, in which case commits that fail to be parsed will be output missing the `data` field (as no fields could be parsed).

See [Parsers](#parsers) below for a list of parsers included with `conventional`.

### Rendering commits into a template

```bash
$ conventional [--config .conventional.yaml] template
```

The `template` command will read a stream of commits, determine different "versions" by looking at the tags on commits, and render them using the configured template. Templates are rendered using Jinja2, and are provided the list of versions along with any custom configuration specified in the configuration file.

See [Templates](#templates) below for a list of templates included with `conventional`.

### Notes

Internally, some commands will use other commands to provide additional functionality and simplify common use-cases.

For example...
```bash
$ conventional list-commits --parse # is equivalent to
$ conventional list-commits | conventional parse-commit
```
And...
```bash
$ conventional template # is equivalent to
$ conventional list-commits | conventional parse-commit | conventional template --input -
```

This means that if, for example, you wish to use `conventional template` but only use commits created since the last tag you can use the command `conventional list-commits --from-last-tag | conventional template --input -`.

## Configuration

Along with the command-line parameters, a configuration file can be provided via the `--config-file` parameter when calling `conventional`. By default `conventional` is configured to parse commits aligning to the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) standard and render them into a changelog, but this can be changed by configuring the `parser` and `template` sections in the config file, along with other things.

See [config_default.yaml](conventional/config_default.yaml) to see what can be included in the configuration file.

Below is a list of the parsers and templates provided by default with `conventional`.

### Parsers

#### [module: conventional.parser, name: ConventionalCommitParser](conventional/parser/conventional_commits.py)
*Parses commits aligning to the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) standard.*

##### Supported configuration:
* `types` - The values which are allowed to be used as a `type` in commit messages. Any commits using a type not specified in this list will fail to parse correctly.

### Templates

#### [package: conventional, name: changelog.md](conventional/templates/changelog.md)
*Renders commits in a format appropriate for a storing in a CHANGELOG.md file.*

##### Supported configuration:
* `commit-link-pattern` - This pattern will be used to generate a link to the commit, with `{rev}` being replaced with the hash of the commit and `{short_rev}` being replace with the short hash of the commit. For example, if you are using Github this may be `https://github.com/[owner]/[repo]/commit/{rev}`.
* `issue-link-pattern` - This pattern will be used to generate a link to any issues references in the commit, with `{issue}` being expanded to the ID of the issue. For example, if you are using Jira this format may be `https://[company].atlassian.net/browse/{issue}`.
* `type-headings` - A mapping of commit "type" to the text that should be used in the header for a specific type of change. Defaults to `{"feat": "Feature", "fix": "Fixes"}`.

#### [package: conventional, name: slack.md](conventional/templates/slack.md)
*Renders commits in a format appropriate for posting to Slack.*

##### Supported configuration:
* `commit-link-pattern` - This pattern will be used to generate a link to the commit, with `{rev}` being replaced with the hash of the commit and `{short_rev}` being replace with the short hash of the commit. For example, if you are using Github this may be `https://github.com/[owner]/[repo]/commit/{rev}`.
* `issue-link-pattern` - This pattern will be used to generate a link to any issues references in the commit, with `{issue}` being expanded to the ID of the issue. For example, if you are using Jira this format may be `https://[company].atlassian.net/browse/{issue}`.
* `type-headings` - A mapping of commit "type" to the text that should be used in the header for a specific type of change. Defaults to `{"feat": "Feature", "fix": "Fixes"}`.
