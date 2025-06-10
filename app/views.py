from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from app import models, serializers, permissions, pagination, throttles

# Create your views here.

class UserViewset(viewsets.ModelViewSet):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = []
    pagination_class = pagination.CustomPagination

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.username = user.email
        user.set_password(serializer.validated_data['password'])
        user.save()
        data = serializers.UserSerializer(user).data
        del data['password']
        return Response('User registered successfully')
    
    def get_permissions(self):
        if self.action in ['create']:
            self.permission_classes = []
        elif self.action in ['update', 'partial_update', 'destroy']:
            print(self.request.user.id)
            self.permission_classes = [IsAuthenticated, permissions.IsUserOwner]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
class BookViewset(viewsets.ModelViewSet):
    queryset = models.Book.objects.all()
    serializer_class = serializers.BookSerializer
    pagination_class = pagination.CustomPagination

    def perform_create(self, serializer):
        if self.request.user.role not in ['author', 'publisher']:
            raise serializers.ValidationError('You need to register as an Author or Publisher to create a new book instance.')
        else:
            #we cannot directly do serializer.save(owner=self.request.user) as we have a M2M relationship not foreign key. instead, we use:
            book = serializer.save() #first save book without any owners
            book.owner.add(self.request.user) #then add the owners thru many-to-many relationship
    
    def get_queryset(self):
        return models.Book.objects.prefetch_related('owner').filter(owner=self.request.user)
    
class ReviewViewset(viewsets.ModelViewSet):
    queryset = models.Review.objects.all()
    serializer_class = serializers.ReviewSerializer
    pagination_class = pagination.CustomPagination
    throttle_classes = [throttles.ReviewCreateThrottle]

    def perform_create(self, serializer):
        serializer.save(owner = self.request.user)