from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.validators import ValidationError
from app import models

class UserSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField(read_only=True)
    avg_book_rating = serializers.ReadOnlyField()
    
    class Meta:
        model = models.User
        fields = ['id', 'name', 'role', 'country', 'bio', 'first_name', 'last_name', 'avg_book_rating']
        extra_kwargs = {
            'first_name': {'write_only': True, 'required': False}, #writeonly allows the fields to not be shown in the response
            'last_name': {'write_only': True, 'required': False}
        }

    def get_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'


class BookSerializer(serializers.ModelSerializer):
    avg_rating = serializers.ReadOnlyField()
    class Meta:
        model = models.Book
        fields = '__all__'
        read_only_fields = ['owner']
    
    def to_representation(self, instance): #can also use methodfield, or nested serializer to achieve this.
        data = super().to_representation(instance)
        data['owner'] = [
            {
            'id': user.id,
            'name': f'{user.first_name} {user.last_name}',
            'role': user.role
            }
            for user in instance.owner.all() #handling many to many
        ]
        return data
    
    #soft deleting books on destroy action
    def delete(self, instance):
        instance.is_deleted = True
        instance.save()
        return Response({'message': 'Book deleted successfully.'})


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Review
        fields = '__all__'
        read_only_fields = ['owner']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        owner = instance.owner
        data['owner'] = {
            'id': owner.id,
            'name': f'{owner.first_name} {owner.last_name}',
            'role': owner.role
        }
        return data
    
    def validate(self, attrs):
        user = self.context['request'].user
        books = attrs.get('book')
        if models.Review.objects.filter(book = books, owner = user).exists():
            raise ValidationError({'Duplicate Review Error': 'You have already reviewed this book. Delete the previous review to readd a new one.'})
        return attrs
    
    def validate_rating(self, value):
        if value > 5:
            raise ValidationError({'Max rating limit exceeded': 'Please rate the book within 1-5 stars.'})
        if value < 1:
            raise ValidationError({'Min rating limit exceeded': 'Please rate the book within 1-5 stars.'})