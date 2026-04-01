from rest_framework.pagination import PageNumberPagination


class CoursePaginator(PageNumberPagination):
    """Пагинатор для списка курсов"""

    page_size = 2  # Количество элементов на странице по умолчанию
    page_size_query_param = "page_size"  # Параметр запроса для изменения количества элементов
    max_page_size = 10  # Максимально допустимое количество элементов на странице
    page_query_param = "page"  # Параметр для указания номера страницы


class LessonPaginator(PageNumberPagination):
    """Пагинатор для списка уроков"""

    page_size = 5  # Количество элементов на странице по умолчанию
    page_size_query_param = "page_size"  # Параметр запроса для изменения количества элементов
    max_page_size = 20  # Максимально допустимое количество элементов на странице
    page_query_param = "page"  # Параметр для указания номера страницы


class DefaultPaginator(PageNumberPagination):
    """Универсальный пагинатор для всех списков"""

    page_size = 3  # Количество элементов на странице по умолчанию
    page_size_query_param = "page_size"
    max_page_size = 15
    page_query_param = "page"
