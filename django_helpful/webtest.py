# Copyright (c) 2015, Raphael Kimmig
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.  Redistributions in binary
# form must reproduce the above copyright notice, this list of conditions and
# the following disclaimer in the documentation and/or other materials provided
# with the distribution.  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS
# AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING,
# BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER
# OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import django_webtest


class WebTest(django_webtest.WebTest):
    def assertFormHasNoErrors(self, response, form_context_name='form', formset_context_name='formset'):
        """Raise error if formset or form with errors is in context"""
        if getattr(response, 'context', None) is None:
            return

        # context doesn't raise if not found
        form = response.context[form_context_name]
        formset = response.context[formset_context_name]

        if not form and not formset:
            return

        error_text = ''
        if form and getattr(form, 'errors', None):
            error_text = "Form contains errors: \n%s\n" % form.errors.as_text()

        if formset and getattr(formset, 'errors', None):
            for index, errors in enumerate(formset.errors):
                if errors:
                    error_text += 'Formset form #%d contains errors: \n%s\n' % (index, errors.as_text())

        if error_text:
            raise AssertionError(error_text)
