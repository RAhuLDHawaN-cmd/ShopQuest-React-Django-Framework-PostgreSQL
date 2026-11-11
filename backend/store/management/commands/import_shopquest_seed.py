import csv
import os
import secrets
from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from store.models import Category, Order, OrderItem, Product, UserProfile


USERS = [
    {"name": "Admin User", "email": "admin@shopquest.com", "role": "admin"},
    {"name": "Maya Patel", "email": "maya@example.com", "role": "user"},
    {"name": "Liam Chen", "email": "liam@example.com", "role": "user"},
    {"name": "Ava Johnson", "email": "ava@example.com", "role": "user"},
]

PRODUCTS = [
    {
        "name": "Wireless Noise-Cancelling Headphones",
        "description": "Immersive sound experience with advanced active noise cancellation.",
        "price": "299.99", "category": "Electronics", "stock": 15,
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        "ratings": "4.8", "num_reviews": 24,
    },
    {
        "name": "Minimalist Modern Chair",
        "description": "A stylish and comfortable addition to any contemporary living room.",
        "price": "150.00", "category": "Furniture", "stock": 30,
        "image_url": "https://images.unsplash.com/photo-1505843490538-5133c6c7d0e1?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        "ratings": "4.2", "num_reviews": 12,
    },
    {
        "name": "Professional DSLR Camera",
        "description": "Capture stunning moments with high-resolution clarity and speed.",
        "price": "1199.99", "category": "Electronics", "stock": 8,
        "image_url": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        "ratings": "4.9", "num_reviews": 50,
    },
    {
        "name": "Classic White Sneakers",
        "description": "Versatile and comfortable, a staple for any casual outfit.",
        "price": "85.00", "category": "Clothing", "stock": 50,
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        "ratings": "4.5", "num_reviews": 89,
    },
    {
        "name": "Smart Fitness Watch",
        "description": "Track workouts, heart rate, and daily activity with a bright touch display.",
        "price": "179.99", "category": "Electronics", "stock": 22,
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        "ratings": "4.6", "num_reviews": 37,
    },
    {
        "name": "Everyday Canvas Backpack",
        "description": "A durable lightweight backpack with room for daily essentials.",
        "price": "59.00", "category": "Accessories", "stock": 40,
        "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        "ratings": "4.4", "num_reviews": 18,
    },
    {
        "name": "Ceramic Table Lamp",
        "description": "A warm, understated accent lamp for a bedside table or reading nook.",
        "price": "74.50", "category": "Home", "stock": 18,
        "image_url": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        "ratings": "4.3", "num_reviews": 9,
    },
    {
        "name": "Stainless Steel Water Bottle",
        "description": "Reusable insulated bottle that keeps drinks cold throughout the day.",
        "price": "28.00", "category": "Accessories", "stock": 65,
        "image_url": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        "ratings": "4.7", "num_reviews": 42,
    },
    {
        "name": "Linen Throw Pillow",
        "description": "A soft textured cushion cover that adds a relaxed touch to your sofa.",
        "price": "34.99", "category": "Home", "stock": 27,
        "image_url": "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        "ratings": "4.1", "num_reviews": 14,
    },
    {
        "name": "Classic Analog Wristwatch",
        "description": "A clean stainless steel watch with a simple, versatile dial.",
        "price": "129.00", "category": "Accessories", "stock": 12,
        "image_url": "https://images.unsplash.com/photo-1524592094714-0f0654e20314?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        "ratings": "4.5", "num_reviews": 31,
    },
]

ORDERS = [
    {
        "user_email": "maya@example.com",
        "items": [
            {"product": "Wireless Noise-Cancelling Headphones", "quantity": 1, "price": "299.99"},
            {"product": "Stainless Steel Water Bottle", "quantity": 2, "price": "28.00"},
        ],
        "total_amount": "355.99",
        "shipping_address": {
            "fullName": "Maya Patel", "street": "12 Linking Road", "city": "Mumbai",
            "postalCode": "400050", "country": "India",
        },
        "payment_reference": "seed_payment_maya_001",
        "status": "Delivered",
    },
    {
        "user_email": "liam@example.com",
        "items": [
            {"product": "Professional DSLR Camera", "quantity": 1, "price": "1199.99"},
            {"product": "Everyday Canvas Backpack", "quantity": 1, "price": "59.00"},
        ],
        "total_amount": "1258.99",
        "shipping_address": {
            "fullName": "Liam Chen", "street": "88 Park Street", "city": "Kolkata",
            "postalCode": "700016", "country": "India",
        },
        "payment_reference": "seed_payment_liam_001",
        "status": "Shipped",
    },
    {
        "user_email": "ava@example.com",
        "items": [
            {"product": "Classic White Sneakers", "quantity": 1, "price": "85.00"},
            {"product": "Minimalist Modern Chair", "quantity": 1, "price": "150.00"},
            {"product": "Ceramic Table Lamp", "quantity": 1, "price": "74.50"},
        ],
        "total_amount": "309.50",
        "shipping_address": {
            "fullName": "Ava Johnson", "street": "5 Residency Road", "city": "Bengaluru",
            "postalCode": "560025", "country": "India",
        },
        "payment_reference": "seed_payment_ava_001",
        "status": "Pending",
    },
]


class Command(BaseCommand):
    help = "Import ShopQuest seed users and products without deleting existing data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show the source record counts without writing to PostgreSQL.",
        )
        parser.add_argument(
            "--credentials-file",
            default=str(Path.home() / ".react-django-seed-credentials.csv"),
            help="Private CSV path for newly generated user passwords.",
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            self.stdout.write(
                f"Would import {len(USERS)} users and {len(PRODUCTS)} products "
                f"(5 categories) plus {len(ORDERS)} orders. Existing records are retained."
            )
            return

        User = get_user_model()
        new_credentials = []
        created_users = 0
        existing_users = 0
        created_profiles = 0
        created_products = 0
        updated_products = 0
        created_categories = 0
        created_orders = 0
        updated_orders = 0
        seed_users = {}

        with transaction.atomic():
            for product_data in PRODUCTS:
                category_name = product_data["category"]
                category, was_created = self._get_category(category_name)
                created_categories += int(was_created)

                fields = {
                    "description": product_data["description"],
                    "price": Decimal(product_data["price"]),
                    "stock": product_data["stock"],
                    "image_url": product_data["image_url"],
                    "ratings": Decimal(product_data["ratings"]),
                    "num_reviews": product_data["num_reviews"],
                }
                product, was_created = Product.objects.get_or_create(
                    category=category,
                    name=product_data["name"],
                    defaults=fields,
                )
                if was_created:
                    created_products += 1
                else:
                    for field, value in fields.items():
                        setattr(product, field, value)
                    product.save(update_fields=list(fields))
                    updated_products += 1

            for user_data in USERS:
                email = user_data["email"]
                first_name, _, last_name = user_data["name"].partition(" ")

                existing = User.objects.filter(
                    email__iexact=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=False,
                    is_superuser=False,
                ).first()
                if existing:
                    existing_users += 1
                    seed_users[email] = existing
                    _, profile_created = UserProfile.objects.get_or_create(user=existing)
                    created_profiles += int(profile_created)
                    continue

                base_username = email[:150]
                username = self._available_username(User, base_username, email)
                password = secrets.token_urlsafe(24)
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=False,
                    is_superuser=False,
                )
                created_users += 1
                seed_users[email] = user
                UserProfile.objects.get_or_create(user=user)
                created_profiles += 1
                new_credentials.append((email, user.username, password))

            for order_data in ORDERS:
                order_fields = {
                    "user": seed_users[order_data["user_email"]],
                    "total_amount": Decimal(order_data["total_amount"]),
                    "shipping_address": order_data["shipping_address"],
                    "payment_reference": order_data["payment_reference"],
                    "status": order_data["status"],
                }
                order, was_created = Order.objects.get_or_create(
                    source_reference=order_data["payment_reference"],
                    defaults=order_fields,
                )
                if was_created:
                    created_orders += 1
                else:
                    for field, value in order_fields.items():
                        setattr(order, field, value)
                    order.save(update_fields=list(order_fields))
                    updated_orders += 1
                    order.items.all().delete()

                for item_data in order_data["items"]:
                    product = Product.objects.get(name=item_data["product"])
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item_data["quantity"],
                        price=Decimal(item_data["price"]),
                    )

        credentials_path = Path(options["credentials_file"]).expanduser()
        if new_credentials:
            self._append_credentials(credentials_path, new_credentials)
            self.stdout.write(
                self.style.WARNING(
                    f"Generated passwords were saved to {credentials_path} "
                    "with owner-only file permissions. Keep this file private."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete: {created_categories} categories created; "
                f"{created_products} products created, {updated_products} updated; "
                f"{created_users} users created, {existing_users} matching regular users kept, "
                f"{created_profiles} profiles created; "
                f"{created_orders} orders created, {updated_orders} updated."
            )
        )
        self.stdout.write("Seed role 'admin' was ignored; imported users have no admin privileges.")

    @staticmethod
    def _get_category(name):
        category = Category.objects.filter(name=name).first()
        if category:
            return category, False

        base_slug = slugify(name) or "category"
        slug = base_slug
        suffix = 2
        while Category.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        return Category.objects.create(name=name, slug=slug), True

    @staticmethod
    def _available_username(User, base_username, email):
        username = base_username
        suffix = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username[:140]}-seed{suffix}"
            suffix += 1
        return username

    @staticmethod
    def _append_credentials(path, credentials):
        path.parent.mkdir(parents=True, exist_ok=True)
        file_exists = path.exists() and path.stat().st_size > 0
        descriptor = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "a", newline="", encoding="utf-8") as output:
                writer = csv.writer(output)
                if not file_exists:
                    writer.writerow(["email", "username", "temporary_password"])
                writer.writerows(credentials)
        except Exception:
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise
