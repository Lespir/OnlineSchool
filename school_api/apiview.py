from rest_framework import generics
from .models import Product
from .serializers import ProductSerializer

from datetime import datetime


class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.filter(start_date__gt=datetime.now())
    serializer_class = ProductSerializer


