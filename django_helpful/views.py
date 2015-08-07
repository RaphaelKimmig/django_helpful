from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from django import forms
from django.contrib import messages
from django.contrib.admin.utils import NestedObjects
from django.core.exceptions import ImproperlyConfigured
from django.forms import modelform_factory, all_valid
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponse
from django.utils.encoding import force_text
from django.views import generic
from django.views.generic import TemplateView
from django.views.generic.base import ContextMixin
from extra_views import SearchableListMixin, SortableListMixin

try:
    from autocomplete_light import ModelForm
except ImportError:
    from django.forms import ModelForm


class FormFieldMixin(object):
    form_fields = None
    form_layout = None

    @classmethod
    def flatten(cls, x):
        result = []
        for el in x:
            if hasattr(el, "__iter__") and not isinstance(el, basestring):
                result.extend(cls.flatten(el))
            elif el is not None:
                result.append(el)
        return result

    def get_form_fields(self):
        return self.form_fields

    @classmethod
    def get_flat_fields(self, fields):
        if fields is None:
            return None

        fields = self.flatten(fields)
        # HACK allow formset delete to be placed
        fields = filter(lambda f: f != 'DELETE', fields)
        return fields

    @classmethod
    def normalize_rows(cls, form_fields):
        rows = []

        for row in form_fields:
            # single field -> single column row
            if isinstance(row, basestring):
                row = ((row, ), )
            elif row and isinstance(row[0], basestring):
                raise ImproperlyConfigured("Rows should be lists of lists, "
                                           "not lists of strings: %s" % cls)
            rows.append(row)
        return rows

    @classmethod
    def construct_form_layout(cls, form_fields):
        row_divs = []
        for row in cls.normalize_rows(form_fields):
            if len(row) == 1:
                col_class = 'col-sm-12'
            elif len(row) == 2:
                col_class = 'col-sm-6'
            elif len(row) == 3:
                col_class = 'col-sm-4'
            else:
                raise ImproperlyConfigured("Row is too long")
            field_divs = (Div(*field, css_class=col_class) for field in row)
            row_div = Div(*field_divs, css_class='row')
            row_divs.append(row_div)
        return Layout(*row_divs)

    def get_form_layout(self):
        if self.form_layout:
            return self.form_layout
        return self.construct_form_layout(self.get_form_fields())

    def get_form_helper(self):
        helper = FormHelper()
        helper.layout = self.get_form_layout()
        helper.form_tag = False
        return helper

    def get_formset(self):
        formset = super(FormFieldMixin, self).get_formset()
        formset.helper = self.get_form_helper()
        formset.helper.render_hidden_fields = True
        return formset

    def get_form_class(self):
        """
        Returns the form class to use in this view.
        """
        if self.form_class:
            return self.form_class
        else:
            # support inline formsets
            if hasattr(self, 'inline_model'):
                model = self.inline_model
            else:
                model = self.model

            if not model:
                raise ImproperlyConfigured(
                    "Please specify either a form_class or model")

            form_fields = self.get_form_fields()
            flat_fields = self.get_flat_fields(form_fields)
            if flat_fields is None:
                raise ImproperlyConfigured(
                    "Please specify either a form_class or form_fields")
            form = modelform_factory(
                model,
                form=ModelForm,
                fields=flat_fields,
                localized_fields=flat_fields,
            )
            form.helper = self.get_form_helper()
            return form


class TitleMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        if getattr(self, 'title', None) and 'title' not in kwargs:
            kwargs['title'] = self.title
        return super(TitleMixin, self).get_context_data(**kwargs)


class ListView(SearchableListMixin, SortableListMixin, generic.ListView):
    paginate_by = 10
    sort_fields = ['id']

    def get_context_data(self, **kwargs):
        kwargs['search_query'] = self.get_search_query() or ''
        if self.model:
            kwargs['model_verbose_name'] = getattr(self.model._meta, 'verbose_name', '')
            kwargs['model_verbose_name_plural'] = getattr(self.model._meta,
                                                          'verbose_name_plural', '')
        return super(ListView, self).get_context_data(**kwargs)


class CreateView(FormFieldMixin, TitleMixin, generic.CreateView):
    def get_context_data(self, **kwargs):
        if self.model:
            kwargs['model_verbose_name'] = getattr(self.model._meta, 'verbose_name', '')
            kwargs['model_verbose_name_plural'] = getattr(self.model._meta,
                                                          'verbose_name_plural', '')
        kwargs['popup'] = self.is_popup()
        return super(CreateView, self).get_context_data(**kwargs)

    def is_popup(self):
        return self.request.GET.get('_popup', '0') == '1'

    def form_valid(self, form):
        response = super(CreateView, self).form_valid(form)
        if self.is_popup():
            response = HttpResponse("""
            <script type="text/javascript">
                opener.dismissAddAnotherPopup(
                    window,
                    "{}",
                    "{}"
                );
            </script>""".format(self.object.pk, self.object))
        return response


class UpdateView(FormFieldMixin, TitleMixin, generic.UpdateView):
    def get_context_data(self, **kwargs):
        if self.model:
            kwargs['model_verbose_name'] = getattr(self.model._meta, 'verbose_name', '')
            kwargs['model_verbose_name_plural'] = getattr(self.model._meta,
                                                          'verbose_name_plural', '')
        return super(UpdateView, self).get_context_data(**kwargs)


class DetailView(generic.DetailView):
    def get_context_data(self, **kwargs):
        if self.model:
            kwargs['model_verbose_name'] = getattr(self.model._meta, 'verbose_name', '')
            kwargs['model_verbose_name_plural'] = getattr(self.model._meta,
                                                          'verbose_name_plural', '')
        return super(DetailView, self).get_context_data(**kwargs)


class DeleteView(generic.DeleteView):
    def can_delete(self, obj):
        return True

    def delete(self, request, *args, **kwargs):
        messages.success(request, u'%s was deleted successfuly.' %
                         self._format_obj(self.get_object()))
        return super(DeleteView, self).delete(request, *args, **kwargs)

    def post(self, *args, **kwargs):
        obj = self.get_object()
        if not self.can_delete(obj):
            return HttpResponseForbidden()
        nested, protected = self.get_nested_objects(obj)
        if protected:
            return HttpResponseForbidden()
        return super(DeleteView, self).post(*args, **kwargs)

    def get_template_names(self):
        names = super(DeleteView, self).get_template_names()
        names.append("seminartool/base_confirm_delete.html")
        return names

    @classmethod
    def get_nested_objects(cls, obj):
        collector = NestedObjects(using='default')
        collector.collect([obj])
        nested = collector.nested(cls._format_obj)
        return nested, map(cls._format_obj, collector.protected)

    @staticmethod
    def _format_obj(obj):
        return u'%s "%s"' % (obj._meta.verbose_name, unicode(obj))

    def get_context_data(self, **kwargs):
        context = super(DeleteView, self).get_context_data(**kwargs)
        nested, protected = self.get_nested_objects(self.get_object())
        context.update({
            'object_name': self._format_obj(self.object),
            'nested_objects': nested,
            'protected_objects': protected,
            'can_delete': self.can_delete(self.object),
        })
        if self.model:
            context['model_verbose_name'] = getattr(self.model._meta, 'verbose_name', '')
        return context


class MultipleObjectCreateView(FormFieldMixin, TemplateView):
    models = None  # [('prefix', Model, ('field1', 'field2'), ('prefix2', Model2, Model2Form), ... ]
    success_url = None
    objects = {}  # a dict mapping names to instances

    @classmethod
    def construct_form_class(cls, model, form_fields):
        flat_fields = cls.get_flat_fields(form_fields)
        form = modelform_factory(
            model,
            form=ModelForm,
            fields=flat_fields,
            localized_fields=flat_fields,
        )

        form.helper = FormHelper()
        form.helper.layout = cls.construct_form_layout(form_fields)
        form.helper.form_tag = False

        return form

    def get_form_kwargs(self, name, **kwargs):
        form_kwargs = {'prefix': name, 'data': self.request.POST or None}
        form_kwargs.update(kwargs)
        return form_kwargs

    def get_forms(self):
        if not self.models:
            raise ImproperlyConfigured("You need to specify the models")

        forms = []
        for name, model, form_fields_or_class in self.models:
            if hasattr(form_fields_or_class, 'is_valid'):
                form_class = form_fields_or_class
            else:
                form_class = self.construct_form_class(model, form_fields_or_class)
            forms.append(form_class(**self.get_form_kwargs(name)))
        return forms

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(forms=self.get_forms(), **kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        forms = self.get_forms()
        if all_valid(forms):
            return self.forms_valid(forms)
        else:
            return self.forms_invalid(forms)

    def forms_valid(self, forms):
        """
        Saves the instances for the supplied forms.
        Has to set self.objects to a dict mapping names to new instances.
        """
        raise NotImplementedError("You need to implement forms_valid yourself")

    def forms_invalid(self, forms):
        context = self.get_context_data(forms=forms, **self.kwargs)
        return self.render_to_response(context)

    def get_success_url(self):
        """
        Returns the supplied success URL.
        """
        if self.success_url:
            # Forcing possible reverse_lazy evaluation
            return force_text(self.success_url)

        if not self.objects:
            raise ImproperlyConfigured("Your forms_valid method should set self.objects")

        for name, __, __ in self.models:
            if name not in self.objects:
                continue

            object = self.objects[name]
            if hasattr(object, 'get_absolute_url'):
                return object.get_absolute_url()

        raise ImproperlyConfigured(
            "No URL to redirect to. Provide a success_url.")


class MultiObjectUpdateView(MultipleObjectCreateView):
    def forms_valid(self, forms):
        for form in forms:
            form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_form_kwargs(self, name, **kwargs):
        kwargs['instance'] = self.objects[name]
        return super(MultiObjectUpdateView, self).get_form_kwargs(name, **kwargs)

    def get_objects(self):
        """Get a dict mapping names from the .models list to instances.

        :return: a dict of {name: instance, other_name: other_instance, ...}
        """
        raise NotImplementedError()

    def get(self, request, *args, **kwargs):
        self.objects = self.get_objects()
        return super(MultiObjectUpdateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.objects = self.get_objects()
        return super(MultiObjectUpdateView, self).post(request, *args, **kwargs)
