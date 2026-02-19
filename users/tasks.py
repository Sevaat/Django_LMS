from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import stripe
from django.conf import settings
from users.models import Payment, Subscription
from users.services import StripeService

stripe.api_key = settings.STRIPE_SECRET_KEY


@shared_task
def check_pending_payments():
    """
    Периодическая задача для проверки статуса ожидающих платежей
    """
    print("Начинаем проверку ожидающих платежей...")

    # Находим все платежи в статусе 'pending', созданные более часа назад
    one_hour_ago = timezone.now() - timedelta(hours=1)
    pending_payments = Payment.objects.filter(
        payment_status='pending',
        pay_date__lte=one_hour_ago
    )

    updated_count = 0
    for payment in pending_payments:
        try:
            if payment.stripe_session_id:
                # Получаем информацию о сессии из Stripe
                session = stripe.checkout.Session.retrieve(payment.stripe_session_id)

                # Обновляем статус платежа
                if session.payment_status == 'paid':
                    payment.payment_status = 'succeeded'
                elif session.payment_status == 'unpaid':
                    payment.payment_status = 'failed'
                elif session.status == 'expired':
                    payment.payment_status = 'failed'

                payment.save()
                updated_count += 1
                print(f"Платеж {payment.id} обновлен, статус: {payment.payment_status}")

        except Exception as e:
            print(f"Ошибка при проверке платежа {payment.id}: {str(e)}")

    print(f"Проверка завершена. Обновлено {updated_count} платежей")
    return f"Обновлено {updated_count} платежей"


@shared_task
def clean_expired_subscriptions():
    """
    Периодическая задача для очистки истекших подписок
    (если у подписок есть срок действия)
    """
    print("Начинаем очистку истекших подписок...")

    total_subscriptions = Subscription.objects.count()
    print(f"Всего активных подписок: {total_subscriptions}")

    return f"Всего подписок: {total_subscriptions}"


@shared_task
def send_payment_reminder(payment_id):
    """
    Задача для отправки напоминания о неоплаченном платеже
    """
    try:
        payment = Payment.objects.get(id=payment_id)
        if payment.payment_status == 'pending':
            print(f"Отправка напоминания о платеже {payment_id} пользователю {payment.user.email}")
            # Здесь можно добавить отправку email
            return f"Напоминание отправлено для платежа {payment_id}"
    except Payment.DoesNotExist:
        print(f"Платеж {payment_id} не найден")
        return f"Ошибка: платеж {payment_id} не найден"


@shared_task
def process_stripe_webhook(event_data):
    """
    Асинхронная обработка webhook от Stripe
    """
    event_type = event_data.get('type')
    print(f"Обработка webhook события: {event_type}")

    if event_type == 'checkout.session.completed':
        session = event_data.get('data', {}).get('object', {})
        payment_id = session.get('client_reference_id')

        if payment_id:
            try:
                payment = Payment.objects.get(id=payment_id)
                payment.payment_status = 'succeeded'
                payment.stripe_payment_intent_id = session.get('payment_intent')
                payment.save()
                print(f"Платеж {payment_id} успешно оплачен")

                return f"Платеж {payment_id} обработан успешно"
            except Payment.DoesNotExist:
                print(f"Платеж {payment_id} не найден")
                return f"Ошибка: платеж {payment_id} не найден"

    elif event_type == 'payment_intent.payment_failed':
        payment_intent = event_data.get('data', {}).get('object', {})
        print(f"Платеж не удался: {payment_intent.get('id')}")

    return f"Событие {event_type} обработано"