{%- with types = config["type-headings"] | read_config({}, dict) %}

{%- for tag, version in versions if version.has_commits() -%}

# {{ tag["name"] | default("Unreleased") }}

{%- for type, changes in version.items() if type is not none and type in types %}

## {{ config["type-headings"][type] | read_config }}

{%- for change in changes if "data" in change %}

{#- #}
-

{%- if "scope" in change["data"]["subject"] %} *{{ change["data"]["subject"]["scope"] }}*:{% endif %}

{#- #} {{ change["data"]["subject"]["message"] }}

{%- with pattern = config["commit-link-pattern"] | read_config(None) %}
{%- if pattern is not none %} ([{{ change["source"]["short_rev"] }}]({{ pattern.format(commit=change["source"]["rev"]) }})){% endif %}
{%- endwith %}

{%- with pattern = config["issue-link-pattern"] | read_config(None) %}
{%- if pattern is not none and change["data"]["metadata"]["closes"] %}, closes
{%- for issue in change["data"]["metadata"]["closes"] %} [{{ issue }}]({{ pattern.format(issue=issue) }}){% endfor %}
{%- endif %}
{%- endwith %}

{%- endfor %}
{%- endfor %}

{% endfor %}

{%- endwith %}