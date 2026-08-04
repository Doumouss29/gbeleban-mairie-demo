import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Crée le superutilisateur depuis DJANGO_SUPERUSER_* s'il n'existe pas."
    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        if not username or not password:
            self.stdout.write("Variables superutilisateur absentes : création ignorée.")
            return
        User = get_user_model()
        user, created = User.objects.get_or_create(username=username, defaults={"email":email,"is_staff":True,"is_superuser":True})
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Superutilisateur {username} créé."))
        else:
            changed = False
            if not user.is_staff: user.is_staff = True; changed = True
            if not user.is_superuser: user.is_superuser = True; changed = True
            if changed: user.save(update_fields=["is_staff","is_superuser"])
            self.stdout.write(f"Superutilisateur {username} déjà présent.")
