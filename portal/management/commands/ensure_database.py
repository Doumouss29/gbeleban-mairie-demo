import os
import re
import psycopg
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Crée la base PostgreSQL cible si elle n'existe pas encore."

    def handle(self, *args, **options):
        if os.environ.get("DB_ENGINE", "postgres").lower() != "postgres":
            self.stdout.write("DB_ENGINE n'est pas postgres : création ignorée.")
            return

        db_name = os.environ.get("DB_NAME", "gbeleban")
        host = os.environ.get("DB_HOST", "").strip()
        port = os.environ.get("DB_PORT", "5432").strip()
        user = os.environ.get("DB_USER", "").strip()
        password = os.environ.get("DB_PASSWORD", "")
        sslmode = os.environ.get("DB_SSLMODE", "require").strip()
        admin_db = os.environ.get("DB_ADMIN_NAME", "postgres").strip()

        if not host or not user or not password:
            raise CommandError("DB_HOST, DB_USER et DB_PASSWORD doivent être renseignés.")

        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", db_name):
            raise CommandError("DB_NAME contient des caractères non autorisés.")

        try:
            with psycopg.connect(
                host=host,
                port=port,
                dbname=admin_db,
                user=user,
                password=password,
                sslmode=sslmode,
                autocommit=True,
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
                    if cur.fetchone():
                        self.stdout.write(self.style.SUCCESS(f"Base PostgreSQL '{db_name}' déjà présente."))
                        return
                    cur.execute(f'CREATE DATABASE "{db_name}"')
                    self.stdout.write(self.style.SUCCESS(f"Base PostgreSQL '{db_name}' créée."))
        except Exception as exc:
            raise CommandError(
                "Impossible de créer automatiquement la base PostgreSQL. "
                f"Vérifie DB_ADMIN_NAME et les droits CREATE DATABASE de DB_USER. Détail: {exc}"
            )
