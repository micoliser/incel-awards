from django.db import models


class OrgPerson(models.Model):
    """Local snapshot of an organization-directory user."""

    class Company(models.TextChoices):
        TOURISM = 'tourism', 'Tourism'
        GLOBAL = 'global', 'Global'
        EXCLUDED = 'excluded', 'Excluded'

    class Electorate(models.TextChoices):
        STAFF = 'staff', 'Staff'
        EXECUTIVE = 'executive', 'Executive'
        INELIGIBLE = 'ineligible', 'Ineligible'

    external_id = models.PositiveIntegerField(unique=True)
    email = models.EmailField(db_index=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    role_code = models.CharField(max_length=64, blank=True, default='')
    role_name = models.CharField(max_length=128, blank=True, default='')
    department_code = models.CharField(max_length=64, blank=True, default='')
    department_name = models.CharField(max_length=128, blank=True, default='')
    unit_name = models.CharField(max_length=128, blank=True, null=True)
    raw_payload = models.JSONField(default=dict, blank=True)

    # Classification cache — recomputed on sync via people.services.classify
    company = models.CharField(
        max_length=16,
        choices=Company.choices,
        default=Company.EXCLUDED,
    )
    electorate = models.CharField(
        max_length=16,
        choices=Electorate.choices,
        default=Electorate.INELIGIBLE,
    )
    is_nigeria_eligible = models.BooleanField(default=False)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Org person'
        verbose_name_plural = 'Org people'

    def __str__(self):
        return f'{self.first_name} {self.last_name} <{self.email}>'

    @property
    def display_name(self):
        return f'{self.first_name} {self.last_name}'.strip()
