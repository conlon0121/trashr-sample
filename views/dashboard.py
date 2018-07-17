import json

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import View
from trashr.forms import DumpsterUpdateForm
from trashr.tables import DumpsterTable
from trashr.models import Dumpster, UserProfile
from trashr.views.utils import get_layer


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(lambda u: UserProfile.objects.get(user=u).org.active,
                                   login_url='/checkout/'), name='get')
class DashboardView(View):
    template_name = "logged_in/dashboard.html"
    form_class = DumpsterUpdateForm

    def get(self, request):
        org = UserProfile.objects.get(user=request.user).org
        dumpsters = Dumpster.objects.filter(org=org)
        layer, lat, long = get_layer(dumpsters)
        table = DumpsterTable(dumpsters)
        return render(request, self.template_name, {'table': table,
                                                    'form_update': self.form_class(),
                                                    'lat': lat,
                                                    'long': long,
                                                    'layer': json.dumps(layer),
                                                    })


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(lambda u: UserProfile.objects.get(user=u).org.active,
                                   login_url='/checkout/'), name='post')
class AlertUpdateView(View):
    form_class = DumpsterUpdateForm

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            form_vals = form.cleaned_data
            Dumpster.objects.filter(id=form_vals['dumpster']).update(alert_percentage=form_vals['percentage'])
            return JsonResponse({"success": 1})
        else:
            return JsonResponse({"success": 0})

