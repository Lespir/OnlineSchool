from rest_framework import serializers
from .models import Product, Lesson



class ProductSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('name', 'author', 'start_date', 'lessons_count', 'price')

    def get_lessons_count(self, obj):
        return Lesson.objects.filter(product=obj).count()
