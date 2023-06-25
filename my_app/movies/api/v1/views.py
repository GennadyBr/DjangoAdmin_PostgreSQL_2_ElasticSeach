from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic.list import BaseListView
from django.views.generic.detail import BaseDetailView

from movies.models import Filmwork


class MoviesApiMixin(BaseListView):
    model = Filmwork
    http_method_names = ('get')

    @staticmethod
    def _list_up_persons(role: str) -> ArrayAgg:
        return ArrayAgg(
            'persons__full_name',
            distinct=True,
            filter=Q(personfilmwork__role=role)
        )

    def get_queryset(self):
        """get_queryset возвращает подготовленный QuerySet"""
        return super().get_queryset(
        ).prefetch_related(
            # prefetch_related перечислить нужные таблицы, предполагает, что нужны все связанные объекты.
            'genres',
            'persons',
        ).values(
            # метод values, превращает QuerySet в словарь.
            'id',
            'title',
            'description',
            'creation_date',
            'rating',
            'type',
        ).annotate(
            # метод annotate, добавляет к полям модели дополнительные значения;
            # Аннотации могут быть рассчитаны из других полей или связей
            # annotate принимает в качестве аргументов название нового поля и метод, который рассчитывает значение
            # Если annotate указан после values, то к результирующему словарю добавляются все данные, рассчитанные в annotate.\
            # В обратном случае вам придётся вручную указывать в values нужные поля из запроса.
            genres=ArrayAgg('genres__name', distinct=True),
            # Postgres - функция ArrayAgg, собирает в список все значения, которые есть у поля;
            actors=self._list_up_persons('actor'),
            directors=self._list_up_persons('director'),
            writers=self._list_up_persons('writer'),
            # Q-объекты передаются в фильтр как позиционные аргументы, умеют инкапсулировать элементы запроса
        ).order_by('title')

    def render_to_response(self, context, **response_kwargs):
        """render_to_response, отвечает за форматирование данных, которые вернутся при GET-запросе"""
        return JsonResponse(context)


class MoviesListApi(MoviesApiMixin):
    """
    класс с тремя методами
    get_queryset, который должен возвращать подготовленный QuerySet;
    get_context_data, возвращающий словарь с данными для формирования страницы;
    render_to_response, отвечающий за форматирование данных, которые вернутся при GET-запросе.
    """

    model = Filmwork
    http_method_names = ('get')  # Список методов, которые реализует обработчик
    paginate_by = 50  # количество объектов на одной странице, например, 50.

    def get_context_data(self, *, object_list=None, **kwargs):
        """get_context_data, возвращает словарь с данными для формирования страницы;"""
        queryset_new = self.get_queryset() #формируем большой queryset и ниже пагинируем-разбиваем на страницы
        paginator, page, queryset, is_paginated = self.paginate_queryset(
            # paginate_queryset() инициализирует пагинатор, применяет его к queryset и возвращает результаты расчёта
            queryset_new,
            self.paginate_by
        )
        return {
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'prev': page.previous_page_number() if page.has_previous() else None,
            'next': page.next_page_number() if page.has_next() else None,
            # 'what is this?': is_paginated, #это True/False
            'results': list(queryset), #в queryset лежит результат пагинации
        }


class MoviesDetailApi(MoviesApiMixin):
    """страница, которая отображает полную информацию об одном фильме"""
    def get_context_data(self, *, object_list=None, **kwargs):
        # return {**kwargs['object']}
        try:
            return {
            'results': list(self.get_queryset().filter(id__icontains=self.kwargs['pk'])),
        }['results'][0]
        except Exception as exc:
            return {'result': 'Invalid ID'}
