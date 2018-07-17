from datetime import timedelta

from dal import autocomplete
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.db.models import F
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import View

from django.shortcuts import render

from trashr.forms import EmailForm, EmailNotificationForm
from trashr.models import UserProfile, Alert, Email, Subscription


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(lambda u: UserProfile.objects.get(user=u).org.active,
                                   login_url='/checkout/'), name='get')
@method_decorator(user_passes_test(lambda u: UserProfile.objects.get(user=u).org.active,
                                   login_url='/checkout/'), name='post')
class PreferencesView(View):
    template_name = "logged_in/preferences.html"
    form_class_add = EmailNotificationForm
    form_class_verify = EmailForm

    def get(self, request):
        profile = UserProfile.objects.get(user=request.user)
        org = profile.org
        emails = Email.objects.filter(org=org, receives_alerts=True)
        alerts = Alert.objects.filter(timestamp__gte=timezone.now() - timedelta(days=30),
                                      dumpster__org=org).prefetch_related('dumpster')\
            .annotate(current_fill=F('dumpster__percent_fill'), address=F('dumpster__address'))
        subscriptions = Subscription.objects.filter(org=org).prefetch_related('plan', 'payment_method', 'transactions')
        return render(request, self.template_name, {'name': org.name,
                                                    'code': org.code,
                                                    'email': profile.email.email,
                                                    'emails': emails,
                                                    'alerts': alerts,
                                                    'stripe_pk': settings.STRIPE_PUBLISHABLE_KEY,
                                                    'subscriptions': subscriptions,
                                                    ''
                                                    'form': self.form_class_add(),
                                                    'form_verify': self.form_class_verify(),
                                                    })

    def post(self, request):
        form = self.form_class_add(request.POST)
        if form.is_valid():
            form_vals = form.cleaned_data
            email = form_vals['email_add']
            try:
                email_obj = Email.objects.get(email=email)
                org = UserProfile.objects.get(user=request.user).org
                if email_obj.org != org:
                    return JsonResponse({'message': 'Invalid email address'}, status=400)
                if email_obj.receives_alerts:
                    return JsonResponse({"message": "Email address already receives alerts"}, status=400)
                email_obj.receives_alerts = True
                email_obj.save()
            except Email.DoesNotExist():
                return JsonResponse({'message': 'Email address does not exist'}, status=400)
            return JsonResponse({'email': email}, status=200)
        return JsonResponse({'message': 'Invalid email address, you may need to refresh the page.' + form.errors}, status=400)


@method_decorator(login_required, name='dispatch')
class EmailDelete(View):
    form_class = EmailForm

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            email = Email.objects.get(email=form.cleaned_data['email'])
            if email.org == UserProfile.objects.get(user=request.user).org:
                email.receives_alerts = False
                email.save()
            else:
                JsonResponse({'message': 'Email not found'}, status=400)
            return JsonResponse({'email': form.cleaned_data['email']}, status=200)
        return JsonResponse({'message': 'Something went wrong'}, status=400)


@method_decorator(login_required, name='dispatch')
class EmailAutoComplete(autocomplete.Select2ListView):
    def get_list(self):
        org = UserProfile.objects.get(user=self.request.user).org
        return Email.objects.filter(org=org, receives_alerts=False).values_list('email', flat=True)
