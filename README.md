django_helpful
==============

Helpful stuff for django development



Helpers
-------
**django_helpful.reverse**

A sane replacemant for djangos `from django.core.urlresolvers.reverse`. 
Do `django_helpful.reverse('view-name', object.pk, param=value)` and it'll do what you mean.



Templatetags
------------


**helpful_tags.query_string**

Creates a query string from the current request updating the specified parameters.

```HTML+Django

{% load helpful_tags %}

<a href="{% query_string page=page_number %}">Go to page {{ page_number }}</a>

```
