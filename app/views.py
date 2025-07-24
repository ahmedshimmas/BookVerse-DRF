from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q, Avg
from rest_framework_simplejwt.authentication import JWTAuthentication
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
            # print(self.request.user.id)
            self.permission_classes = [IsAuthenticated, permissions.IsUserOwner]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def good_authors(self, request):
        good_authors = models.User.objects.annotate(avg_book_rating = Avg('books__reviews__rating')).filter(avg_book_rating__gte=3).prefetch_related('books')
        serializer = self.get_serializer(good_authors, many=True)
        return Response(serializer.data)
    
class BookViewset(viewsets.ModelViewSet):
    queryset = models.Book.objects.all()
    serializer_class = serializers.BookSerializer
    pagination_class = pagination.CustomPagination
    authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        if self.request.user.role not in ['author', 'publisher']:
            raise serializers.ValidationError('You need to register as an Author or Publisher to create a new book instance.')
        else:
            #we cannot directly do serializer.save(owner=self.request.user) as we have a M2M relationship not foreign key. instead, we use:
            book = serializer.save() #first save book without any owners
            book.owner.add(self.request.user) #then add the owners thru many-to-many relationship
    
    def get_queryset(self):
        return models.Book.objects.prefetch_related('owner').filter(owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def great_books(self, request):
        great_books = models.Book.objects.annotate(avg_rating = Avg('reviews__rating')).filter(avg_rating__gte=3).prefetch_related('reviews')
        print(great_books.query)
        serializer = self.get_serializer(great_books, many=True)
        return Response(serializer.data)
    
class ReviewViewset(viewsets.ModelViewSet):
    queryset = models.Review.objects.all()
    serializer_class = serializers.ReviewSerializer
    pagination_class = pagination.CustomPagination
    throttle_classes = [throttles.ReviewCreateThrottle]
    authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        serializer.save(owner = self.request.user)