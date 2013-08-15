django_helpful
==============

Helpful stuff for django development
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Provides a sane replacemant for djangos `from django.core.urlresolvers.reverse`
Just do `django_helpful.reverse('view-name', object.pk)` and it'll do what you want it to.


```HTML+Django:

{% load helpful_tags %}

<a href="{% query_string page=page_number %}">Go to page {{ page_number }}</a>
{# creates a query string from the current request with only page number updated #}
```
