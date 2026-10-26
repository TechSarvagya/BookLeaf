"""Import the supplied JSON without changing credentials on repeat runs."""
import json
from decimal import Decimal
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from accounts.models import User, AuthorProfile
from books.models import Book

DEMO_PASSWORD = 'BookleafDemo123!'
DEMO_ADMIN_EMAIL = 'admin@bookleaf.demo'

class Command(BaseCommand):
    help = 'Import supplied BookLeaf demo authors and books idempotently.'
    def add_arguments(self, parser):
        parser.add_argument('--file', required=True)
        parser.add_argument('--password', default=DEMO_PASSWORD)
        parser.add_argument('--allow-production-demo', action='store_true')

    def handle(self, *args, **options):
        if not settings.DEBUG and not options['allow_production_demo']:
            raise CommandError('Demo seeding in production requires --allow-production-demo.')
        path = Path(options['file'])
        if not path.is_file(): raise CommandError(f'Dataset not found: {path}')
        try: authors = json.loads(path.read_text(encoding='utf-8'))['authors']
        except (ValueError, KeyError, TypeError) as exc: raise CommandError('Expected JSON with an authors array.') from exc
        if not isinstance(authors, list): raise CommandError('Expected an authors array.')
        count = 0
        with transaction.atomic():
            for author in authors:
                email = author['email'].lower()
                user, created = User.objects.get_or_create(email=email, defaults={
                    'full_name': author['name'], 'role': 'AUTHOR'})
                if not created and user.role != 'AUTHOR':
                    raise CommandError(f'Existing non-author account conflicts with {email}.')
                if created:
                    user.set_password(options['password']); user.save(update_fields=['password'])
                profile, _ = AuthorProfile.objects.update_or_create(
                    author_id=str(author['author_id']),
                    defaults={'user':user,'phone':author.get('phone') or '',
                              'city':author.get('city') or '',
                              'joined_date':author.get('joined_date') or None})
                for raw in author.get('books', []):
                    def amount(name, nullable=False):
                        value = raw.get(name)
                        return None if nullable and value is None else Decimal(str(value or 0))
                    fields = {name: raw.get(name) for name in [
                        'title','isbn','genre','status','print_partner']}
                    fields.update(author=profile,
                                  publication_date=raw.get('publication_date') or None,
                                  mrp=amount('mrp',True),
                                  author_royalty_per_copy=amount('author_royalty_per_copy',True),
                                  total_copies_sold=raw.get('total_copies_sold') or 0,
                                  total_royalty_earned=amount('total_royalty_earned'),
                                  royalty_paid=amount('royalty_paid'),
                                  royalty_pending=amount('royalty_pending'),
                                  last_royalty_payout_date=raw.get('last_royalty_payout_date') or None,
                                  available_on=raw.get('available_on') or [])
                    Book.objects.update_or_create(book_id=str(raw['book_id']),defaults=fields)
                    count += 1
            admin, created = User.objects.get_or_create(email=DEMO_ADMIN_EMAIL,
                defaults={'full_name':'BookLeaf Demo Admin','role':'ADMIN','is_staff':True})
            if not created and admin.role != 'ADMIN':
                raise CommandError('Existing account conflicts with demo admin email.')
            if created:
                admin.set_password(options['password']); admin.save(update_fields=['password'])
        self.stdout.write(self.style.SUCCESS(f'Imported {len(authors)} authors and {count} books. Existing passwords were preserved.'))
