---
permalink: /
title: "Haoran (Leo) Liu"
author_profile: true
redirect_from:
  - /about/
  - /about.html
---

{% include base_path %}
{% assign bank = site.data.bank %}

{{ bank.profile.bio_long | markdownify }}

**Research interests:** {{ bank.profile.interests | join: " · " }}

Selected publications
======
<ul>
{% for category in site.publication_category %}{% for p in site.publications reversed %}{% if p.category != category[0] %}{% continue %}{% endif %}{% unless p.selected %}{% continue %}{% endunless %}
  <li>
    <a href="{{ base_path }}{{ p.url }}"><b>{{ p.title }}</b></a><br/>
    <small>{{ p.citation }}</small>
    {% if p.paperurl %} <a href="{{ p.paperurl }}">[paper]</a>{% endif %}
  </li>
{% endfor %}{% endfor %}
</ul>
<a href="{{ base_path }}/publications/">All publications →</a>

Selected projects
======
{% assign projects = site.portfolio | sort: "order" %}
{% for post in projects %}
  {% include archive-single.html %}
{% endfor %}
<a href="{{ base_path }}/portfolio/">All projects →</a>
