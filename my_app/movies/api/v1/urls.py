from django.urls import path
from . import views

urlpatterns = [
    path('movies/', views.MoviesListApi.as_view()),
    # Так как MoviesListApi — это класс, а path ожидает на вход функцию,
    # необходимо использовать специальный метод класса as_view,
    # который вернёт функцию-обёртку вашего класса
    path('movies/<uuid:pk>', views.MoviesDetailApi.as_view()),
]