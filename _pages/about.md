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
{% assign pubs = site.publications | sort: "date" | reverse %}
<ul>
{% for p in pubs %}
  <li>
    <a href="{{ base_path }}{{ p.url }}"><b>{{ p.title }}</b></a><br/>
    <small>{{ p.citation }}</small>
    {% if p.paperurl %} <a href="{{ p.paperurl }}">[paper]</a>{% endif %}
  </li>
{% endfor %}
</ul>
<a href="{{ base_path }}/publications/">All publications →</a>

Selected projects
======
{% for item in site.portfolio %}
  {% include archive-single.html %}
{% endfor %}
<a href="{{ base_path }}/portfolio/">All projects →</a>
