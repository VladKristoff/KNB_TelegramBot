import telebot
import config
from telebot import types
from random import choice
import sqlite3
import os

bot = telebot.TeleBot(f'{config.TOKEN}')

# Получаем список команд
def set_bot_commands():
    commands = [
        types.BotCommand('start', "Запустить бота"),
        types.BotCommand('help', "Помощь и правила"),
        types.BotCommand('stats', "Мой профиль"),
        types.BotCommand('reset', "Сбросить статистику"),
    ]
    bot.set_my_commands(commands)

# Функция получения статистики пользователей
def get_users_stats(user_id, username):
    conn = sqlite3.connect('data\data.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if user == None:
        # Создаём нового пользователя
        cursor.execute('INSERT INTO users (user_id, username, wins, losses, draws) VALUES (?, ?, 0, 0, 0)', (user_id, username))
        conn.commit()
        stats = {'wins': 0, 'losses': 0, 'draws': 0}
    else:
        stats = stats = {'wins': user[2], 'losses': user[3], 'draws': user[4]}

    conn.close()
    return stats

# Обновление статистики пользователя
def update_user_stats(user_id, result):
    conn = sqlite3.connect('data\data.db')
    cursor = conn.cursor()

    if result == 'win':
        cursor.execute('UPDATE users SET wins = wins + 1 WHERE user_id = ?', (user_id,))

    elif result == 'lose':
        cursor.execute('UPDATE users SET losses = losses + 1 WHERE user_id = ?', (user_id,))
    
    else:
        cursor.execute("UPDATE users SET draws = draws + 1 WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

def reset_user_stats(user_id):
    conn = sqlite3.connect('data\data.db')
    cursor = conn.cursor()

    conn.execute('UPDATE users SET wins = 0, losses = 0, draws = 0 WHERE user_id = ?', (user_id,))

    conn.commit()
    conn.close()

set_bot_commands()

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    get_users_stats(user_id, username)

    bot.send_message(message.chat.id, 'Чтобы просмотреть возможные команды, используйте /help')

    # Создание клавиатуры и кнопок
    keyboard = types.ReplyKeyboardMarkup(row_width=1)
    button1 = types.KeyboardButton("Камень ✊")
    button2 = types.KeyboardButton("Ножницы ✌️")
    button3 = types.KeyboardButton("Бумага ✋")
    keyboard.add(button1, button2, button3) # Добавление кнопок на клавиатуру

    bot.reply_to(message, 'Игра "Камень, ножницы, бумага", выбери вариант на клавиатуре', reply_markup=keyboard)

# Просмотр возможных команд
@bot.message_handler(commands=['help'])
def help(message):
    help_text = """
🎮 Правила игры:
• Камень бьет ножницы
• Ножницы бьют бумагу  
• Бумага бьет камень

Команды:
/help - информация об игре
/stats - просмотр статистики
/reset - сброс статистики
"""
    bot.send_message(message.chat.id, help_text)
    
# Просмотр счёта
@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    user_is_premium = getattr(message, 'is_premium', False)

    stats = get_users_stats(user_id, username)

    total_games = stats['wins'] + stats['losses'] + stats['draws']

    if stats['wins'] > 0:
        wins_perc = stats['wins'] / total_games * 100
    else:
        wins_perc = 0

    stats_info = f"""
👤 Ваш профиль:
Имя: {message.from_user.first_name}
ID: {user_id}
Username: {username}
Premium: {"✅ Да" if user_is_premium else "❌ Нет"}

📊 Ваша статистика:
Побед: {stats['wins']} 🎉
Поражений: {stats['losses']} 😢
Ничьих: {stats['draws']} 😐
Всего игр: {total_games}

Процент побед: {wins_perc:.1f}% 📈
    """

    bot.send_message(message.chat.id, stats_info)

# Сброс счёта
@bot.message_handler(commands=['reset'])
def reset(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    stats = get_users_stats(user_id, username)
    total_games = stats['wins'] + stats['losses'] + stats['draws']

    if total_games == 0:
        bot.send_message(message.chat.id, 'Ваша статистика и так пуста')

    else:
        reset_user_stats(user_id)
        bot.send_message(message.chat.id, '✅ Ваша статистика успешно сброшена')


# Игра "Камень, ножницы, бумага"
@bot.message_handler(content_types=['text'])
def handle_message(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    choices = ["Камень ✊", "Ножницы ✌️", "Бумага ✋"]
    user_choice = message.text
    computer_choice = choice(choices)

    if user_choice not in choices:
        bot.send_message(message.chat.id, 'Пожалуйста, выберите вариант из списка')
        return

    else:
        bot.send_message(message.chat.id, f'Компьютер выбрал: "{computer_choice}"') # Показываю, что выбрал копмьютер
        bot.send_message(message.chat.id, f'Вы выбрали: "{user_choice}"') # Показываю, что выбрал пользователь
        if user_choice == computer_choice:
            bot.send_message(message.chat.id, 'Ничья')
            result = 'draw'

        elif (user_choice == "Камень ✊" and computer_choice == "Ножницы ✌️") or \
              (user_choice == "Бумага ✋" and computer_choice == "Камень ✊") or \
              (user_choice == "Ножницы ✌️" and computer_choice == "Бумага ✋"):
            bot.send_message(message.chat.id, 'Вы выйграли')
            result = 'win'

        else:
            bot.send_message(message.chat.id, 'Вы проиграли')
            result = 'lose'
    
    update_user_stats(user_id, result)
    get_users_stats(user_id, username)


if __name__ == '__main__':
    print("Бот запущен")
    bot.remove_webhook()
    bot.polling(non_stop=True)