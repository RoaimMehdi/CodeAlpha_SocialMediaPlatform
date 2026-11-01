from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Post, Comment, Follow, Like, Profile

User = get_user_model()

class UserMiniSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'avatar', 'bio')

    def get_avatar(self, obj):
        try:
            if hasattr(obj, 'profile') and obj.profile.avatar:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.profile.avatar.url)
                return obj.profile.avatar.url
        except Exception:
            pass
        return None

    def get_bio(self, obj):
        try:
            if hasattr(obj, 'profile'):
                return obj.profile.bio
        except Exception:
            pass
        return ''


class ProfileSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    followers_count = serializers.ReadOnlyField()
    following_count = serializers.ReadOnlyField()
    posts_count = serializers.ReadOnlyField()
    avatar_url = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = (
            'id', 'user', 'bio', 'avatar', 'avatar_url',
            'created_at', 'followers_count', 'following_count',
            'posts_count', 'is_following'
        )
        read_only_fields = ('created_at',)

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user == obj.user:
                return False
            return Follow.objects.filter(follower=request.user, following=obj.user).exists()
        return False


import re

class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=False, default='', style={'input_type': 'password'})
    email = serializers.EmailField(required=True)
    full_name = serializers.CharField(write_only=True, required=False, default='')

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'full_name')

    def validate_username(self, value):
        # Automatically clean and convert spaces to underscores (e.g., 'Roaim Mehdi' -> 'roaim_mehdi')
        cleaned = re.sub(r'\s+', '_', value.strip()).lower()
        if not re.match(r'^[a-zA-Z0-9_@.+-]+$', cleaned):
            raise serializers.ValidationError("Enter a valid username using letters, numbers, and underscores.")
        if User.objects.filter(username__iexact=cleaned).exists():
            raise serializers.ValidationError(f"The username '{cleaned}' is already taken.")
        return cleaned

    def validate(self, attrs):
        pw = attrs.get('password')
        pw_confirm = attrs.get('password_confirm') or pw
        if pw != pw_confirm:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        if User.objects.filter(email__iexact=attrs['email']).exists():
            raise serializers.ValidationError({"email": "This email is already registered."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        full_name = validated_data.pop('full_name', '')
        first_name = full_name.split()[0] if full_name else ''
        last_name = ' '.join(full_name.split()[1:]) if full_name and len(full_name.split()) > 1 else ''

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=first_name,
            last_name=last_name
        )
        Profile.objects.get_or_create(user=user)
        return user


class CommentSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'post', 'author', 'content', 'created_at')
        read_only_fields = ('author', 'created_at')


class PostSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    likes_count = serializers.ReadOnlyField()
    comments_count = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            'id', 'author', 'title', 'content', 'image', 'image_url',
            'created_at', 'updated_at', 'comments', 'comments_count',
            'likes_count', 'is_liked'
        )
        read_only_fields = ('author', 'created_at', 'updated_at')

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class FollowSerializer(serializers.ModelSerializer):
    follower = UserMiniSerializer(read_only=True)
    following = UserMiniSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ('id', 'follower', 'following', 'created_at')


class LikeSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ('id', 'user', 'post', 'created_at')
