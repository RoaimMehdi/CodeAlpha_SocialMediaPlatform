from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Profile, Post, Comment, Follow, Like

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds initial users, profiles, posts, comments, likes, and follows'

    def handle(self, *args, **options):
        self.stdout.write("Seeding sample social media data...")

        # Setup admin password
        admin_user, _ = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com'})
        admin_user.set_password('admin123')
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.save()
        admin_profile, _ = Profile.objects.get_or_create(user=admin_user)
        admin_profile.bio = "Platform Administrator & System Architect 🚀"
        admin_profile.save()

        # Demo Users
        users_data = [
            {
                'username': 'sarah_tech',
                'email': 'sarah@example.com',
                'bio': 'Full-stack software engineer | Cloud & Python enthusiast 💻✨',
            },
            {
                'username': 'alex_ux',
                'email': 'alex@example.com',
                'bio': 'Product Designer crafting fluid digital experiences & micro-interactions 🎨',
            },
            {
                'username': 'zayd_ai',
                'email': 'zayd@example.com',
                'bio': 'AI Researcher exploring LLMs, agentic workflows, and neural compute 🤖⚡',
            },
            {
                'username': 'emma_wander',
                'email': 'emma@example.com',
                'bio': 'Photographer & nomad. Capturing raw light and cityscapes 📸🌄',
            }
        ]

        created_users = [admin_user]
        for u in users_data:
            user, created = User.objects.get_or_create(username=u['username'], defaults={'email': u['email']})
            user.set_password('password123')
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.bio = u['bio']
            profile.save()
            created_users.append(user)

        # Sample Posts
        posts_data = [
            {
                'author': created_users[1], # sarah_tech
                'title': 'Excited to launch our new microservices pipeline!',
                'content': 'Just finished migrating our core indexing service to asynchronous workers. Reduced API latency by 64%! Performance optimization is always worth the effort. #Django #Backend #Python',
            },
            {
                'author': created_users[2], # alex_ux
                'title': 'Dark Mode & Glassmorphism Design Trends in 2026',
                'content': 'Clean typography, subtle neon accents, and well-tuned opacity transforms make web apps feel like high-end native software. What is your favorite UI detail to polish? #UIUX #WebDesign #DesignSystem',
            },
            {
                'author': created_users[3], # zayd_ai
                'title': 'Autonomous Agents and Code Synthesis',
                'content': 'We are entering the era of self-correcting agent loops. Instead of just generating code snippets, systems test, trace, and refine their own logic iteratively. The developer becomes the conductor. #AI #Tech #Future',
            },
            {
                'author': created_users[4], # emma_wander
                'title': 'Morning golden hour in Kyoto',
                'content': 'Woke up at 5:00 AM to catch the quiet mist above the bamboo grove. Travel teaches you to slow down and observe every detail. #Photography #Travel #Japan',
            },
            {
                'author': admin_user,
                'title': 'Welcome to Connectly!',
                'content': 'Welcome everyone to Connectly Mini Social Platform! Explore user profiles, share your updates, like and comment on community posts, and connect with fellow creators. #Community #Welcome',
            }
        ]

        posts = []
        for p in posts_data:
            post, _ = Post.objects.get_or_create(
                author=p['author'],
                content=p['content'],
                defaults={'title': p['title']}
            )
            posts.append(post)

        # Sample Comments
        Comment.objects.get_or_create(
            post=posts[0],
            author=created_users[2],
            defaults={'content': 'Incredible latency drop! Are you using Celery or Redis Queues?'}
        )
        Comment.objects.get_or_create(
            post=posts[0],
            author=created_users[1],
            defaults={'content': 'Redis Streams with async worker pools! Works like a charm.'}
        )
        Comment.objects.get_or_create(
            post=posts[1],
            author=created_users[3],
            defaults={'content': 'Subtle borders with 8% opacity and backdrop blur make all the difference!'}
        )
        Comment.objects.get_or_create(
            post=posts[2],
            author=admin_user,
            defaults={'content': 'Spot on. Agentic loops are redefining software engineering.'}
        )

        # Sample Likes
        Like.objects.get_or_create(user=admin_user, post=posts[0])
        Like.objects.get_or_create(user=created_users[2], post=posts[0])
        Like.objects.get_or_create(user=created_users[3], post=posts[0])
        Like.objects.get_or_create(user=created_users[1], post=posts[1])
        Like.objects.get_or_create(user=admin_user, post=posts[1])
        Like.objects.get_or_create(user=created_users[2], post=posts[2])
        Like.objects.get_or_create(user=created_users[4], post=posts[2])

        # Sample Follows
        Follow.objects.get_or_create(follower=admin_user, following=created_users[1])
        Follow.objects.get_or_create(follower=admin_user, following=created_users[2])
        Follow.objects.get_or_create(follower=created_users[1], following=admin_user)
        Follow.objects.get_or_create(follower=created_users[2], following=created_users[1])
        Follow.objects.get_or_create(follower=created_users[3], following=created_users[1])
        Follow.objects.get_or_create(follower=created_users[4], following=created_users[2])

        self.stdout.write(self.style.SUCCESS("Social media sample data seeded successfully!"))
