from rest_framework import serializers
from .models import Category, Product

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    # This adds the readable category name to the JSON, not just the ID number
    category_name = serializers.ReadOnlyField(source='category.name')
    image_url = serializers.SerializerMethodField()

    def get_image_url(self, product):
        if product.image:
            image_url = product.image.url
        else:
            image_url = product.image_url or None
        request = self.context.get("request")
        return request.build_absolute_uri(image_url) if request and image_url else image_url

    class Meta:
        model = Product
        fields = '__all__'