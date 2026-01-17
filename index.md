---
layout: single
title: מתכונים משפחתיים
permalink: /
classes: wide
---

ברוכים הבאים לאתר המתכונים המשפחתי.  
מתכונים ביתיים, ברורים ונוחים לבישול.

---

{% include recipe-filter.html %}


## כל המתכונים


<div class="recipes-grid">

{% assign sorted = site.recipes | sort: "title" %}
{% for recipe in sorted %}
  <div class="recipe-card" data-category="{{ recipe.category }}">
    <a href="{{ recipe.url | relative_url }}" class="recipe-card-link">

      {% if recipe.image and recipe.image != "" %}
        <div class="recipe-card-image-wrapper">
          <img
            src="{{ recipe.image | relative_url }}"
            alt="{{ recipe.title }}"
            loading="lazy"
            class="recipe-card-image">
        </div>
      {% else %}
        <div class="recipe-card-image-wrapper empty"></div>
      {% endif %}

      <div class="recipe-card-body">
        <h3 class="recipe-card-title">{{ recipe.title }}</h3>

        {% if recipe.description %}
          <p class="recipe-card-desc">{{ recipe.description }}</p>
        {% endif %}
      </div>

    </a>
  </div>
{% endfor %}

</div>


<script>
  document.getElementById('recipe-filter').addEventListener('change', function () {
    const value = this.value;
    document.querySelectorAll('.recipe-card').forEach(card => {
      if (value === 'all' || card.dataset.category === value) {
        card.style.display = '';
      } else {
        card.style.display = 'none';
      }
    });
  });
</script>
