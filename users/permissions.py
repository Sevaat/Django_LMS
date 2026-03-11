from rest_framework import permissions


class IsModer(permissions.BasePermission):
    """
    Проверка, является ли пользователь модератором
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name="moders").exists()


class IsOwner(permissions.BasePermission):
    """
    Проверка, является ли пользователь владельцем объекта
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and obj.owner == request.user


class IsNotModer(permissions.BasePermission):
    """
    Проверка, что пользователь НЕ является модератором
    Используется для ограничения создания контента модераторами
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and not request.user.groups.filter(name="moders").exists()


class IsModerOrOwner(permissions.BasePermission):
    """
    Проверка, является ли пользователь модератором или владельцем
    Комбинированное разрешение для удобства
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (
            request.user.groups.filter(name="moders").exists() or obj.owner == request.user
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение только для чтения для всех, изменение только для админов
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff
