from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegisterView,
    CurrentUserView,
    UserProfileView,
    SuggestedUsersView,
    ToggleFollowView,
    UserFollowersView,
    UserFollowingView,
    PostViewSet,
    CommentViewSet
)

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = [
    # Auth endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', CurrentUserView.as_view(), name='current_user'),

    # Direct aliases for standard simplejwt & register endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_alias'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh_alias'),
    path('register/', RegisterView.as_view(), name='register_alias'),

    # User & Social endpoints
    path('users/suggested/', SuggestedUsersView.as_view(), name='suggested_users'),
    path('users/<str:username>/', UserProfileView.as_view(), name='user_profile'),
    path('users/<str:username>/toggle-follow/', ToggleFollowView.as_view(), name='toggle_follow'),
    path('users/<str:username>/followers/', UserFollowersView.as_view(), name='user_followers'),
    path('users/<str:username>/following/', UserFollowingView.as_view(), name='user_following'),

    # Posts & Comments via Router
    path('', include(router.urls)),
]
