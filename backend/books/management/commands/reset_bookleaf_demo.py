"""Explicitly clear demo conversations, guarded to local development only."""
import json
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from accounts.models import AuthorProfile
from tickets.models import Ticket

class Command(BaseCommand):
    help = 'Delete tickets, messages and notes for supplied demo authors in local development.'
    def add_arguments(self, parser):
        parser.add_argument('--confirm', action='store_true')
        parser.add_argument('--file', required=True)
    def handle(self, *args, **options):
        if not settings.DEBUG: raise CommandError('Demo reset is disabled when BOOKLEAF_DEBUG=False.')
        if not options['confirm']: raise CommandError('Pass --confirm to delete demo ticket conversations.')
        path=Path(options['file'])
        if not path.is_file(): raise CommandError(f'Dataset not found: {path}')
        try: external_ids=[str(item['author_id']) for item in json.loads(path.read_text(encoding='utf-8'))['authors']]
        except (ValueError,KeyError,TypeError) as exc: raise CommandError('Invalid demo dataset.') from exc
        with transaction.atomic():
            author_ids = AuthorProfile.objects.filter(author_id__in=external_ids).values_list('id',flat=True)
            count,_ = Ticket.objects.filter(author_id__in=author_ids).delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} demo ticket-related records; authors and books remain.'))
