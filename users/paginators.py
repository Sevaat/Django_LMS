from rest_framework.pagination import PageNumberPagination


class UserPaginator(PageNumberPagination):
    """Пагинатор для списка пользователей"""

    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 20
    page_query_param = 'page'


class PaymentPaginator(PageNumberPagination):
    """Пагинатор для списка платежей"""

    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
    page_query_param = 'page'


class SubscriptionPaginator(PageNumberPagination):
    """Пагинатор для списка подписок"""

    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 20
    page_query_param = 'page'