from django import forms


class PayerRedirectForm(forms.Form):

    def __init__(self, *args, **kwargs):

        self.redirect_data = kwargs.pop('redirect_data', {})

        super(PayerRedirectForm, self).__init__()

        for name, value in self.redirect_data.iteritems():
            self.fields[name] = forms.CharField(widget=forms.HiddenInput(), initial=value)
