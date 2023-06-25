from django.urls import include, path
# from movies.api.v1 import views

urlpatterns = [
    path('v1/', include('movies.api.v1.urls')),  # for API/v1
    # path('movies/', views.MoviesListApi.as_view()),
    # Так как MoviesListApi — это класс, а path ожидает на вход функцию, необходимо использовать специальный метод класса as_view, который вернёт функцию-обёртку вашего класса
]
