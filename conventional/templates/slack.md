{%- with types = config["type-headings"] | read_config({}, dict) %}
{%- for tag, version in versions if version.has_commits() %}

{%- if loop.previtem is defined %}

{% endif %}

{%- with pattern = config["version-link-pattern"] | read_config(None) %}
{%- if pattern is none or tag is none -%}
# {{ tag["name"] | default("Unreleased") }}
{%- else -%}
# [{{ tag["name"] | default("Unreleased") }}]({{ pattern.format(tag=tag["name"]) }})
{%- endif %}
{%- endwith %}

{%- with pattern = config["compare-link-pattern"] | read_config(None) %}
{%- if pattern is not none and tag is not none and loop.nextitem is defined %}
{%- with next_tag, _ = loop.nextitem %}
_Compare with [{{ next_tag["name"] }}]({{ pattern.format(to=tag["name"], from=next_tag["name"]) }})_
{%- endwith %}
{%- endif %}
{%- endwith %}

{%- for type, changes in version.items() if type is not none and type in types %}

## {{ config["type-headings"][type] | read_config }}

{%- for change in changes if "data" in change %}

{#- #}
-

{%- if "scope" in change["data"]["subject"] %} *{{ change["data"]["subject"]["scope"] }}:*{% endif %}

{#- #} {{ change["data"]["subject"]["message"] }}

{%- with pattern = config["commit-link-pattern"] | read_config(None) %}
{%- if pattern is not none %} ([{{ change["source"]["short_rev"] }}]({{ pattern.format(commit=change["source"]["rev"]) }})){% endif %}
{%- endwith %}

{%- with pattern = config["issue-link-pattern"] | read_config(None) %}
{%- if pattern is not none and change["data"]["metadata"]["closes"] %}, closes
{%- for issue in change["data"]["metadata"]["closes"] %} [{{ issue }}]({{ pattern.format(issue=issue) }}){% endfor %}
{%- endif %}
{%- endwith %}

{%- with footers = change["data"].get("body", {}).get("footer", {}).get("items", []) %}
{%- with release_notes = footers | selectattr("key", "eq", "Release-Notes") | map(attribute="value") %}
{%- for notes in release_notes %}

  {{ notes | indent(width=2) }}
{%- endfor %}
{%- endwith %}

{%- with breaking_changes = footers | selectattr("key", "eq", "BREAKING CHANGE") | map(attribute="value") %}
{%- for notes in breaking_changes %}

  *BREAKING CHANGE:* {{ notes | indent(width=2) }}
{%- endfor %}
{%- endwith %}
{%- endwith %}

{%- endfor %}
{%- endfor %}

{%- endfor %}

{%- endwith %}