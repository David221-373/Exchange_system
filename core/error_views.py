"""Кастомные страницы HTTP-ошибок. 401 и 503 — также по URL /errors/401/ и /errors/503/ (Django не регистрирует для них handler по умолчанию)."""

from django.shortcuts import render

_ERROR_CTX = "errors/http_error.html"


def bad_request(request, exception=None):
    return render(
        request,
        _ERROR_CTX,
        {
            "code": 400,
            "title": "Некорректный запрос",
            "subtitle": "Сервер не смог обработать запрос. Проверьте адрес или попробуйте с главной страницы.",
        },
        status=400,
    )


def permission_denied(request, exception=None):
    return render(
        request,
        _ERROR_CTX,
        {
            "code": 403,
            "title": "Доступ запрещён",
            "subtitle": "У вас нет прав для просмотра этой страницы. Обратитесь к администратору при необходимости.",
        },
        status=403,
    )


def page_not_found(request, exception=None):
    return render(
        request,
        _ERROR_CTX,
        {
            "code": 404,
            "title": "Страница не найдена",
            "subtitle": "Такой страницы не существует или ссылка устарела.",
        },
        status=404,
    )


def server_error(request):
    return render(
        request,
        _ERROR_CTX,
        {
            "code": 500,
            "title": "Ошибка сервера",
            "subtitle": "Что-то пошло не так. Попробуйте позже или напишите в поддержку.",
        },
        status=500,
    )


def unauthorized_demo(request):
    return render(
        request,
        _ERROR_CTX,
        {
            "code": 401,
            "title": "Требуется авторизация",
            "subtitle": "Войдите в аккаунт, чтобы открыть этот раздел.",
        },
        status=401,
    )


def service_unavailable_demo(request):
    return render(
        request,
        _ERROR_CTX,
        {
            "code": 503,
            "title": "Технические работы",
            "subtitle": "Сервис временно недоступен. Загляните чуть позже — мы уже чиним.",
        },
        status=503,
    )
