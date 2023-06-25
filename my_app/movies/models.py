# Create your models here.

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class TimeStampedMixin(models.Model):
    # auto_now_add автоматически выставит дату создания записи
    created_at = models.DateTimeField(auto_now_add=True)
    # auto_now изменятся при каждом обновлении записи
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Этот параметр указывает Django, что этот класс не является представлением таблицы
        abstract = True


class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class GenreFilmwork(UUIDMixin):
    film_work = models.ForeignKey('Filmwork', on_delete=models.CASCADE)
    genre = models.ForeignKey('Genre', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content\".\"genre_film_work"


class PersonFilmwork(UUIDMixin):
    class Role(models.TextChoices): # выбор для поля role
        ACTOR = 'AC', _('Actor')
        DIRECTOR = 'DR', _('Director')
        WRITER = 'WR', _('Writer')
        OPERATOR = 'OP', _('Operator')
        PRODUCER = 'PR', _('Producer')

    film_work = models.ForeignKey('Filmwork', on_delete=models.CASCADE)
    person = models.ForeignKey('Person', on_delete=models.CASCADE)
    role = models.CharField(
        max_length=12,
        choices=Role.choices,
        default=Role.ACTOR,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content\".\"person_film_work"
        indexes = [
            models.Index(fields=['film_work', 'person', 'role']),
        ]



class Genre(UUIDMixin, TimeStampedMixin):
    def __str__(self):
        return self.name

    # Типичная модель в Django использует число в качестве id. В таких ситуациях поле не описывается в модели.
    # Вам же придётся явно объявить primary key.
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Первым аргументом обычно идёт человекочитаемое название поля
    name = models.CharField(_('name'), max_length=255)
    # blank=True делает поле необязательным для заполнения.
    description = models.TextField(_('description'), blank=True, null=True)

    class Meta:
        # Ваши таблицы находятся в нестандартной схеме. Это нужно указать в классе модели
        db_table = "content\".\"genre"
        # Следующие два поля отвечают за название модели в интерфейсе
        verbose_name = _('Genre')
        verbose_name_plural = _('Genres')


class Person(UUIDMixin, TimeStampedMixin):
    def __str__(self):
        return self.full_name

    full_name = models.CharField(_('Full Name'), max_length=255)

    class Meta:
        db_table = "content\".\"person"
        verbose_name = _('Person')
        verbose_name_plural = _('Persons')


class Filmwork(UUIDMixin, TimeStampedMixin):
    def __str__(self):
        return self.title

    class TypeFilm(models.TextChoices):
        MOVIE = 'MV', _('movie')
        TV_SHOW = 'TV', _('tv_show')

    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), max_length=555, blank=True, null=True)
    creation_date = models.DateField(blank=True, null=True)
    # поле для переноса данных из SQLite (хотя там вроде все данные NULL)
    file_path = models.TextField(_('file_path'), max_length=255, blank=True, null=True)
    # rating - рейтинг фильмов с валидатором от 0 до 100
    rating = models.FloatField(_('rating'), blank=True, null=True,
                               validators=[MinValueValidator(0),
                                           MaxValueValidator(100)])
    # type - выбор Movie или TV Show?
    type = models.CharField(
        max_length=8,
        choices=TypeFilm.choices,
    )

    genres = models.ManyToManyField(Genre, through='GenreFilmwork')
    persons = models.ManyToManyField(Person, through='PersonFilmwork')

    class Meta:
        # Ваши таблицы находятся в нестандартной схеме. Это нужно указать в классе модели
        db_table = "content\".\"film_work"

        # НЕПОНЯЛ ЗАМЕЧЕНИЕ РЕВЬЮЕРА
        # class Meta описан в GenreFilmwork и PersonFilmwork
        """    class Meta: 
                db_table = "content"."genre_film_work"
                db_table = "content"."person_film_work" """

        indexes = [
            models.Index(fields=['creation_date']),
        ]

        # Следующие два поля отвечают за название модели в интерфейсе
        verbose_name = _('Film')
        verbose_name_plural = _('Films')
