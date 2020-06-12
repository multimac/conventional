# Changelog

{%- with types = config["types"] | read_config({}, dict) %}

{%- for tag, version in versions if version.has_commits() %}

## {{ tag["name"] | default("Unreleased") }}

{%- for type, changes in version.items() if type is not none and type in types %}

### {{ config["types"][type] | read_config }}

{%- for change in changes if "data" in change %}

{#- #}
-

{%- if "scope" in change["data"]["subject"] %} **{{ change["data"]["subject"]["scope"] }}**:{% endif %}

{#- #} {{ change["data"]["subject"]["message"] }}

{%- with pattern = config["commit-pattern"] | read_config(None) %}
{%- if pattern is not none %} ([{{ change["source"]["short_rev"] }}]({{ pattern.format(commit=change["source"]["rev"]) }})){% endif %}
{%- endwith %}

{%- with pattern = config["issue-pattern"] | read_config(None) %}
{%- if pattern is not none and change["data"]["metadata"]["closes"] %}, closes
{%- for issue in change["data"]["metadata"]["closes"] %} [{{ issue }}]({{ pattern.format(issue=issue) }}){% endfor %}
{%- endif %}
{%- endwith %}

{%- with footers = change["data"].get("body", {}).get("footer", {}).get("items", []) %}
{%- with release_notes = footers | selectattr("key", "eq", "Release-Notes") | map(attribute="value") | first %}
{%- if release_notes %}

  {{ release_notes | indent(width=2) }}
{%- endif %}
{%- endwith %}
{%- endwith %}

{%- endfor %}
{%- endfor %}

{%- endfor %}

{%- endwith %}