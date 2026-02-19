import stripe
from django.conf import settings
from decimal import Decimal

# Инициализация Stripe с секретным ключом
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Сервис для работы с платежной системой Stripe"""

    @staticmethod
    def create_product(name, description=None):
        """
        Создание продукта в Stripe

        Args:
            name: Название продукта
            description: Описание продукта

        Returns:
            stripe.Product: Объект продукта
        """
        try:
            product = stripe.Product.create(
                name=name,
                description=description,
                type='good'
            )
            return product
        except stripe.error.StripeError as e:
            raise Exception(f"Ошибка создания продукта в Stripe: {str(e)}")

    @staticmethod
    def create_price(amount, currency='rub', product_id=None, product_name=None):
        """
        Создание цены для продукта в Stripe

        Args:
            amount: Сумма в рублях (будет преобразована в копейки)
            currency: Валюта (rub, usd, eur)
            product_id: ID продукта в Stripe (если продукт уже создан)
            product_name: Название продукта (если продукт не создан)

        Returns:
            stripe.Price: Объект цены
        """
        try:
            # Преобразуем сумму в копейки
            amount_in_cents = int(amount * 100)

            # Если передан product_name, сначала создаем продукт
            if product_name and not product_id:
                product = StripeService.create_product(product_name)
                product_id = product.id

            price = stripe.Price.create(
                unit_amount=amount_in_cents,
                currency=currency,
                product=product_id,
            )
            return price
        except stripe.error.StripeError as e:
            raise Exception(f"Ошибка создания цены в Stripe: {str(e)}")

    @staticmethod
    def create_checkout_session(price_id, success_url, cancel_url, client_reference_id=None):
        """
        Создание сессии для оплаты

        Args:
            price_id: ID цены в Stripe
            success_url: URL для перенаправления после успешной оплаты
            cancel_url: URL для перенаправления при отмене оплаты
            client_reference_id: ID платежа в нашей системе для связи

        Returns:
            stripe.Checkout.Session: Объект сессии
        """
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=client_reference_id,
            )
            return session
        except stripe.error.StripeError as e:
            raise Exception(f"Ошибка создания сессии оплаты: {str(e)}")

    @staticmethod
    def retrieve_session(session_id):
        """
        Получение информации о сессии оплаты

        Args:
            session_id: ID сессии в Stripe

        Returns:
            stripe.Checkout.Session: Объект сессии
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except stripe.error.StripeError as e:
            raise Exception(f"Ошибка получения сессии: {str(e)}")

    @staticmethod
    def retrieve_payment_intent(payment_intent_id):
        """
        Получение информации о платеже

        Args:
            payment_intent_id: ID PaymentIntent в Stripe

        Returns:
            stripe.PaymentIntent: Объект платежа
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return payment_intent
        except stripe.error.StripeError as e:
            raise Exception(f"Ошибка получения платежа: {str(e)}")

    @staticmethod
    def create_payment_for_course(course, user, amount, success_url, cancel_url):
        """
        Создание полного цикла оплаты для курса

        Args:
            course: Объект курса
            user: Объект пользователя
            amount: Сумма оплаты
            success_url: URL успеха
            cancel_url: URL отмены

        Returns:
            dict: Информация о созданном платеже и ссылка на оплату
        """
        try:
            # 1. Создаем продукт в Stripe
            product = StripeService.create_product(
                name=course.name,
                description=course.description
            )

            # 2. Создаем цену в Stripe
            price = StripeService.create_price(
                amount=amount,
                currency='rub',
                product_id=product.id
            )

            # 3. Создаем сессию для оплаты
            session = StripeService.create_checkout_session(
                price_id=price.id,
                success_url=success_url,
                cancel_url=cancel_url
            )

            return {
                'stripe_product_id': product.id,
                'stripe_price_id': price.id,
                'stripe_session_id': session.id,
                'payment_url': session.url,
                'session': session
            }
        except Exception as e:
            raise Exception(f"Ошибка создания платежа: {str(e)}")


def create_stripe_product(course):
    """Упрощенная функция для создания продукта из курса"""

    return StripeService.create_product(
        name=course.name,
        description=course.description
    )


def create_stripe_price(amount, product_id):
    """Упрощенная функция для создания цены"""

    return StripeService.create_price(
        amount=amount,
        currency='rub',
        product_id=product_id
    )


def create_stripe_session(price_id, payment_id):
    """Упрощенная функция для создания сессии оплаты"""

    success_url = "http://localhost:8000/users/payments/success/?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = "http://localhost:8000/users/payments/cancel/"

    return StripeService.create_checkout_session(
        price_id=price_id,
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(payment_id)
    )