from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Post, Comment, Follow, Like, Profile
from .serializers import (
    RegisterSerializer,
    UserMiniSerializer,
    ProfileSerializer,
    PostSerializer,
    CommentSerializer,
    FollowSerializer,
    LikeSerializer
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens for instant login
        refresh = RefreshToken.for_user(user)
        profile, _ = Profile.objects.get_or_create(user=user)
        profile_data = ProfileSerializer(profile, context={'request': request}).data

        return Response({
            'user': profile_data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'message': 'Account created successfully.'
        }, status=status.HTTP_201_CREATED)


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        
        # Check name update
        name = request.data.get('name') or request.data.get('full_name')
        if name:
            parts = str(name).strip().split()
            request.user.first_name = parts[0]
            request.user.last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
            request.user.save()

        # Check bio update
        bio = request.data.get('bio')
        if bio is not None:
            profile.bio = bio
            
        # Check avatar update
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']

        profile.save()
        serializer = ProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        profile, _ = Profile.objects.get_or_create(user=user)
        serializer = ProfileSerializer(profile, context={'request': request})
        
        # Fetch user's posts
        posts = Post.objects.filter(author=user)
        posts_serializer = PostSerializer(posts, many=True, context={'request': request})
        
        return Response({
            'profile': serializer.data,
            'posts': posts_serializer.data
        })


class SuggestedUsersView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        if request.user.is_authenticated:
            # Users who are not the current user and not already followed
            following_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
            suggested = User.objects.exclude(id=request.user.id).exclude(id__in=following_ids)[:20]
        else:
            suggested = User.objects.all()[:20]

        profiles = [Profile.objects.get_or_create(user=u)[0] for u in suggested]
        serializer = ProfileSerializer(profiles, many=True, context={'request': request})
        return Response(serializer.data)


class ToggleFollowView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, username):
        target_user = get_object_or_404(User, username=username)
        if target_user == request.user:
            return Response({'detail': 'You cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        follow_instance = Follow.objects.filter(follower=request.user, following=target_user)
        target_profile, _ = Profile.objects.get_or_create(user=target_user)

        if follow_instance.exists():
            follow_instance.delete()
            return Response({
                'is_following': False,
                'followers_count': target_profile.followers_count,
                'detail': f'Unfollowed {username}'
            }, status=status.HTTP_200_OK)
        else:
            Follow.objects.create(follower=request.user, following=target_user)
            return Response({
                'is_following': True,
                'followers_count': target_profile.followers_count,
                'detail': f'Followed {username}'
            }, status=status.HTTP_201_CREATED)


class UserFollowersView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        follows = Follow.objects.filter(following=user).select_related('follower')
        followers_users = [f.follower for f in follows]
        profiles = [Profile.objects.get_or_create(user=u)[0] for u in followers_users]
        serializer = ProfileSerializer(profiles, many=True, context={'request': request})
        return Response(serializer.data)


class UserFollowingView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        follows = Follow.objects.filter(follower=user).select_related('following')
        following_users = [f.following for f in follows]
        profiles = [Profile.objects.get_or_create(user=u)[0] for u in following_users]
        serializer = ProfileSerializer(profiles, many=True, context={'request': request})
        return Response(serializer.data)


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        queryset = Post.objects.all().select_related('author', 'author__profile').prefetch_related('comments', 'likes')
        feed_filter = self.request.query_params.get('feed')
        author_username = self.request.query_params.get('author')
        search_query = self.request.query_params.get('search')

        if author_username:
            queryset = queryset.filter(author__username=author_username)
        elif feed_filter == 'following' and self.request.user.is_authenticated:
            following_ids = Follow.objects.filter(follower=self.request.user).values_list('following_id', flat=True)
            queryset = queryset.filter(author_id__in=following_ids)

        if search_query:
            queryset = queryset.filter(
                Q(content__icontains=search_query) |
                Q(title__icontains=search_query) |
                Q(author__username__icontains=search_query)
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user and not request.user.is_staff:
            return Response({'detail': 'You can only delete your own posts.'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        existing_like = Like.objects.filter(user=request.user, post=post)

        if existing_like.exists():
            existing_like.delete()
            is_liked = False
            detail = 'Unliked post'
        else:
            Like.objects.create(user=request.user, post=post)
            is_liked = True
            detail = 'Liked post'

        return Response({
            'is_liked': is_liked,
            'likes_count': post.likes_count,
            'detail': detail
        }, status=status.HTTP_200_OK)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Comment.objects.all().select_related('author', 'author__profile')

    def get_queryset(self):
        queryset = super().get_queryset()
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user and comment.post.author != request.user and not request.user.is_staff:
            return Response({'detail': 'You do not have permission to delete this comment.'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
