from django.db import models
from django.contrib.auth.models import AbstractUser

# ----------------------------------------
# Custom User Model with Role Field
# ----------------------------------------
class User(AbstractUser):
    ROLE_CHOICES = (
        ('author', 'Author'),
        ('publisher', 'Publisher'),
        ('reader', 'Reader'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='reader')
    email = models.EmailField(unique=True)
    country = models.CharField(max_length=100)
    bio = models.TextField(blank=True, null=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.role})"

# ----------------------------------------
# Book Model
# ----------------------------------------
class Book(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    owner = models.ManyToManyField(User, related_name='books')
    published_date = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.title}'


# ----------------------------------------
# Review Model
# ----------------------------------------
class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # class Meta:
        # unique_together = ('book', 'owner') #ensures a user can only review a book once, returns a unique constraint error if violated
        #if you do not want the server to crash and return a custom response, can achieve using serializer validations

    def __str__(self):
        return f"{self.book.title} - {self.rating}⭐ by {self.owner.username}"
