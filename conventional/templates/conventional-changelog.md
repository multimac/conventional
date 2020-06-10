{% for tag, changes in versions %}
{%- if not changes %}{% continue %}{% endif -%}

## {{ tag["name"] | default("Unreleased") }}

{%- for type, commits in changes.items() %}
{%- if type is none %}{% continue %}{% endif %}
{%- if type not in (config["types"] | read_config({}, dict)) %}{% continue %}{% endif %}

### {{ config["types"][type] | read_config }}

{%- for commit in commits %}
{% if "parsed" not in commit %}{% continue %}{% endif -%}

-
{%- if "scope" in commit["parsed"]["subject"] %} **{{ commit["parsed"]["subject"]["scope"] }}**: {% endif %}

{{- commit["parsed"]["subject"]["message"] }}

{%- with pattern = config["commit-pattern"] | read_config(None) %}
{%- if pattern is not none %} ([{{ commit["commit"]["short_rev"] }}]({{ pattern.format(commit=commit["commit"]["rev"]) }})){% endif %}
{%- endwith %}

{%- with pattern = config["issue-pattern"] | read_config(None) %}
{%- if pattern is not none and commit["parsed"]["metadata"]["closes"] %}, closes
{%- for issue in commit["parsed"]["metadata"]["closes"] %} [{{ issue }}]({{ pattern.format(issue=issue) }}){% endfor %}
{%- endif %}
{%- endwith %}

{%- endfor %}
{%- endfor %}

{% endfor %}