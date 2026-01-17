---
layout: default
title: מתכונים משפחתיים
---

## רשימת מתכונים

{% assign sorted = site.recipes | sort: "title" %}
{% for recipe in sorted %}
- [{{ recipe.title }}]({{ recipe.url | relative_url }})
{% endfor %}
