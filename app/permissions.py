from django.db import models
from django.db.models import Q
from rest_framework.permissions import BasePermission

class IsUserOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.id == request.user.id

class IsObjectOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if hasattr(obj, 'owner'): 
            if isinstance(obj.owner, models.Manager): #isinstance checks whether an object is part of a class of a model manager? e.g. isinstance(5, int) will return True
                return user in obj.owner.all()
            return obj.owner == user
        return False