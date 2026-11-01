from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from core.models import Profile, Post, Comment, Follow, Like
from datetime import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with realistic demo users, posts, and social interactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete existing demo data first',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options.get('flush'):
            self.stdout.write('Flushing existing demo data...')
            Follow.objects.all().delete()
            Comment.objects.all().delete()
            Like.objects.all().delete()
            Post.objects.all().delete()
            User.objects.filter(username__in=[
                'admin', 'ali_khan', 'sara_ahmed', 'usman_dev', 'ayesha_k',
                'hamza_codes', 'zainab_art', 'bilal_travels', 'fatima_foodie',
                'sarah_tech', 'alex_ux', 'zayd_ai', 'emma_wander'
            ]).delete()

        self.stdout.write('Creating administrator account...')
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
        )
        admin_user.set_password('admin123')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        admin_profile, _ = Profile.objects.get_or_create(user=admin_user)
        admin_profile.bio = 'Connectly Platform Administrator & Lead Architect 🚀'
        admin_profile.save()

        self.stdout.write('Creating demo creators...')
        demo_users_data = [
            ('ali_khan', 'Ali Khan', 'ali_khan@example.com', 'Senior Full-Stack Developer & Open Source Enthusiast 💻⚡'),
            ('sara_ahmed', 'Sara Ahmed', 'sara_ahmed@example.com', 'UI/UX & Product Designer. Crafting minimalist design systems 🎨✨'),
            ('usman_dev', 'Usman Tariq', 'usman_dev@example.com', 'Backend Engineer. Python, Django, Distributed Systems & Docker 🐳'),
            ('ayesha_k', 'Ayesha Malik', 'ayesha_k@example.com', 'Data Scientist & Machine Learning researcher. Exploring NLP & LLMs 🧠📊'),
            ('hamza_codes', 'Hamza Rauf', 'hamza_codes@example.com', 'Mobile & Web Dev. Flutter, React, and building products in public 🚀'),
            ('zainab_art', 'Zainab Qazi', 'zainab_art@example.com', 'Digital Artist & Creative Director. Visual storytelling & 3D art 🖌️🌈'),
            ('bilal_travels', 'Bilal Hassan', 'bilal_travels@example.com', 'Traveler, Photographer & Storyteller. 40+ countries and counting 🌍✈️'),
            ('fatima_foodie', 'Fatima Noor', 'fatima_foodie@example.com', 'Food Blogger & Culinary Explorer. Sharing authentic recipes & food reviews 🍜🍰')
        ]

        user_objs = {}
        for username, full_name, email, bio in demo_users_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email, 'first_name': full_name.split()[0], 'last_name': ' '.join(full_name.split()[1:])}
            )
            user.set_password('Demo@1234')
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.bio = bio
            profile.save()
            user_objs[username] = user
            self.stdout.write(f'  Created user: {username}')

        self.stdout.write('Creating realistic posts...')
        posts_data = [
            ('ali_khan', 'Modern Architecture', 'Just migrated our relational database cluster with zero downtime. Optimized queries and indexing gave us an 80% reduction in average latency! #Databases #Django #Architecture'),
            ('sara_ahmed', 'Design Principles', 'Typography and intentional negative space will always outperform loud animations. A clean visual rhythm lets content breathe and keeps users focused. #Design #UI #UX'),
            ('usman_dev', 'Python Concurrency', 'Exploring Python 3.13 free-threaded builds with asyncio. The developer experience keeps getting better with every release! #Python #AsyncIO #Engineering'),
            ('ayesha_k', 'AI & Embeddings', 'Benchmarking vector database retrieval accuracy on domain-specific datasets. Deterministic evaluation pipelines make all the difference. #AI #MachineLearning #DataScience'),
            ('hamza_codes', 'Building in Public', 'Launched our new API service today! Built with Django REST Framework and deployed in containers. Grateful for this amazing builder community! #BuildingInPublic #DRF #WebDev'),
            ('zainab_art', 'Creative Workflow', 'Working on a new brand identity and color palette system. Finding the perfect balance between contrast, accessibility, and elegance. #Creative #Branding #Design'),
            ('bilal_travels', 'Northern Heights', 'Sunrise over the Karakoram mountains. Crisp morning air, silence, and breathtaking peaks as far as the eye can see. Pure serenity. #Travel #Photography #Nature'),
            ('fatima_foodie', 'Culinary Secrets', 'The secret to authentic slow-cooked curry: caramelize the onions patiently on low flame until rich golden-brown. Technique matters more than spice count! #Cooking #Foodie #Recipes')
        ]

        created_posts = []
        for author_uname, title, content in posts_data:
            post, _ = Post.objects.get_or_create(
                author=user_objs[author_uname],
                content=content,
                defaults={'title': title}
            )
            created_posts.append(post)

        self.stdout.write('Adding social likes & follows...')
        all_users = list(user_objs.values())
        for post in created_posts:
            # Add likes
            for u in all_users[:4]:
                Like.objects.get_or_create(user=u, post=post)

        # Cross follows
        for i, u1 in enumerate(all_users):
            for j, u2 in enumerate(all_users):
                if i != j and (i + j) % 2 == 0:
                    Follow.objects.get_or_create(follower=u1, following=u2)

        # Add comments
        if created_posts:
            Comment.objects.get_or_create(
                post=created_posts[0],
                author=user_objs['usman_dev'],
                defaults={'content': 'Incredible performance boost! Proper indexing is often underappreciated.'}
            )
            Comment.objects.get_or_create(
                post=created_posts[1],
                author=user_objs['ali_khan'],
                defaults={'content': 'Totally agree, clean UI and high legibility always win in the long run.'}
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded demo users, posts, and social relationships!'))
