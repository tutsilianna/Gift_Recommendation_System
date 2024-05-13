from dataclasses import dataclass

from environs import Env


@dataclass
class TgBot:
    token: str             # Токен для доступа к телеграм-боту
    admins_id: list[int]   # Список id администраторов бота

@dataclass
class Config:
    tg_bot: TgBot


# Создаем функцию, которая будет читать файл .env и возвращать
# экземпляр класса Config с заполненными полями token и admins_id
def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(
        tg_bot=TgBot(
            token=env('BOT_TOKEN'),
            admins_id=list(map(int, env.list('ADMINS_ID')))
        )
    )