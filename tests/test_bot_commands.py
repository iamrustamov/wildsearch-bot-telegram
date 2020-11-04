from unittest.mock import patch

import pytest
from envparse import env


@pytest.mark.parametrize('message', [
    ['https://www.wildberries.ru/brands/la-belle-femme'],
    ['https://www.wildberries.ru/promotions/eeh-mix-uhod-i-parfyumeriya'],
    ['https://www.wildberries.ru/catalog/dom-i-dacha/tovary-dlya-remonta/instrumenty/magnitnye-instrumenty'],
    ['https://www.wildberries.ru/catalog/0/search.aspx?subject=99&search=сапоги&sort=popular'],
    ['https://www.wildberries.ru/search?text=одеяло%201,5%20спальное'],
])
@patch('src.tasks.schedule_category_export.apply_async')
def test_command_catalog_correct(mocked_celery_delay, web_app, telegram_json_message, message):
    telegram_json = telegram_json_message(message=str(message))

    web_app.simulate_post('/' + env('TELEGRAM_API_TOKEN'), body=telegram_json)

    mocked_celery_delay.assert_called()


@pytest.mark.skip
@pytest.mark.parametrize('message', [
    ['https://www.wildberries.ru/catalog/dom-i-dacha/tovary-dlya-remonta/instrumenty/magnitnye-instrumenty'],
    ['https://www.wildberries.ru/catalog/0/search.aspx?subject=99&search=сапоги&sort=popular'],
])
@patch('telegram.Bot.send_message')
def test_command_catalog_maintenance(mocked_bot_send_message, web_app, telegram_json_message, message):
    telegram_json = telegram_json_message(message=str(message))

    web_app.simulate_post('/' + env('TELEGRAM_API_TOKEN'), body=telegram_json)

    assert 'Наш сервис обновляется' in mocked_bot_send_message.call_args.kwargs['text']


@pytest.mark.parametrize('message, expected_text', [
    ['https://www.ozon.ru/category/elektronika-15500/', 'пока не поддерживаются'],
    ['https://beru.ru/catalog/vytiazhki/80444/list?hid=90581', 'пока не поддерживаются'],
    ['https://goods.ru/catalog/avtosvet/', 'пока не поддерживаются'],
    ['https://www.lamoda.ru/c/21/shoes-sapogi/?sitelink=topmenuW&l=5', 'пока не поддерживаются'],
    ['https://tmall.ru/ru/__pc/pages/sda_appliances.htm', 'пока не поддерживаются'],
    ['https://www.wildberries.ru/catalog/12365745/detail.aspx?targetUrl=GP', 'указали неправильную команду'],
])
@patch('telegram.Bot.send_message')
def test_wrong_catalog_commands(mocked_bot_send_message, message, expected_text, web_app, telegram_json_message):
    telegram_json = telegram_json_message(message=str(message))

    web_app.simulate_post('/' + env('TELEGRAM_API_TOKEN'), body=telegram_json)

    assert expected_text in mocked_bot_send_message.call_args.kwargs['text']


@patch('src.tasks.schedule_category_export.apply_async')
@patch('telegram.Bot.send_message')
def test_command_catalog_throttled_wb(mocked_bot_send_message, mocked_celery_delay, web_app, telegram_json_message, create_telegram_command_logs):
    create_telegram_command_logs(5, 'wb_catalog', 'https://www.wildberries.ru/catalog/knigi-i-diski/kantstovary/tochilki')
    telegram_json = telegram_json_message(message='https://www.wildberries.ru/catalog/dom-i-dacha/tovary-dlya-remonta/instrumenty/magnitnye-instrumenty')

    web_app.simulate_post('/' + env('TELEGRAM_API_TOKEN'), body=telegram_json)

    assert 'Ваш лимит запросов закончился.' in mocked_bot_send_message.call_args.kwargs['text']


@pytest.mark.parametrize('message_text, expected_text', [
    ['ℹ️ О сервисе', 'Этот телеграм бот поможет собирать данные о товарах на Wildberries'],
    ['🚀 Увеличить лимит запросов', 'Если вы хотите увеличить или снять лимит запросов'],
    ['Я просто мимокрокодил', 'Непонятная команда'],
])
@patch('telegram.Bot.send_message')
def test_reply_messages(mocked_bot_send_message, web_app, telegram_json_message, message_text, expected_text):
    telegram_json = telegram_json_message(message=str(message_text))

    web_app.simulate_post('/' + env('TELEGRAM_API_TOKEN'), body=telegram_json)

    assert expected_text in mocked_bot_send_message.call_args.kwargs['text']


@pytest.mark.parametrize('command, expected_text', [
    ['/start', 'Этот телеграм бот поможет собирать данные о товарах'],
    ['/help', 'Этот телеграм бот поможет собирать данные о товарах'],
])
@patch('telegram.Bot.send_message')
def test_reply_commands(mocked_reply_text, web_app, telegram_json_command, command, expected_text):
    telegram_json = telegram_json_command(command=command)

    web_app.simulate_post('/' + env('TELEGRAM_API_TOKEN'), body=telegram_json)

    mocked_reply_text.assert_called()
    assert expected_text in mocked_reply_text.call_args.kwargs['text']


@pytest.mark.parametrize('callback, expected_text', [
    ['keyboard_help_catalog_link', 'скопируйте из адресной строки браузера ссылку'],
    ['keyboard_analyse_category', 'Анализ выбранной категории'],
    ['keyboard_help_info_feedback', 'напишите нам весточку'],
])
@patch('telegram.Bot.send_message')
def test_reply_callbacks(mocked_bot_send_message, web_app, telegram_json_callback, callback, expected_text):
    telegram_json = telegram_json_callback(callback=callback)

    web_app.simulate_post('/' + env('TELEGRAM_API_TOKEN'), body=telegram_json)

    assert expected_text in mocked_bot_send_message.call_args.kwargs['text']
