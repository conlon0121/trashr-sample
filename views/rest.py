import stripe
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from trashr.serializers import ReadingSerializer, TransactionSerializer


class CreateReading(APIView):

    @staticmethod
    def post(request):
        try:
            if not request.user.is_superuser:
                return HttpResponse(status=400)
        except User.DoesNotExist:
            return HttpResponse(status=400)

        serializer = ReadingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.validated_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateTransaction(APIView):

    @staticmethod
    def post(request):
        endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
            serializer = TransactionSerializer(data=event)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.validated_data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except ValueError as e:
            # Invalid payload
            return Response(e, status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return Response(e, status=400)
