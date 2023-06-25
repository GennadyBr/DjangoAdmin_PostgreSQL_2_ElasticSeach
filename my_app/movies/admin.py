from django.contrib import admin
from .models import Genre, Filmwork, Person, GenreFilmwork, PersonFilmwork
from django.utils.translation import gettext_lazy as _


# Register your models here.


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    # search_fields = ['question_GenreAdmin']

    # Отображение полей в списке
    list_display = ('name', 'created_at', 'updated_at')
    verbose_list_display = _('name'), _('created_at'), _('updated_at')

    # Фильтрация в списке
    list_filter = ('created_at',)

    # Поиск по полям
    search_fields = ('name', 'description', 'id')


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    # search_fields = ['question_PersonAdmin']

    # Отображение полей в списке
    list_display = ('full_name', 'created_at', 'updated_at')

    # Фильтрация в списке
    list_filter = ('created_at',)

    # Поиск по полям
    search_fields = ('full_name', 'id')


class GenreFilmworkInline(admin.TabularInline):
    model = GenreFilmwork
    autocomplete_fields = ('genre',)  # автозаполнение ссылается на поле genre


class PersonFilmworkInline(admin.TabularInline):
    model = PersonFilmwork
    autocomplete_fields = ('person',)  # автозаполнение ссылается на поле person


@admin.register(Filmwork)
class FilmworkAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        queryset = (
            super()
            .get_queryset(request)
            .prefetch_related(*self.list_prefetch_related)
        )
        return queryset

    def get_genres(self, obj):
        return ', '.join([genre.name for genre in obj.genres.all()])

    inlines = (GenreFilmworkInline, PersonFilmworkInline,)

    # Отображение полей в списке
    get_genres.short_description = 'Жанры фильма'
    list_prefetch_related = ('genres',)
    list_display = ('title', 'type', 'creation_date', 'get_genres', 'file_path', 'rating', 'created_at', 'updated_at',)

    # Фильтрация в списке
    list_filter = ('type',)

    # Поиск по полям
    search_fields = ('title', 'description', 'id')

