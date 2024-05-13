from dataclasses import dataclass
from environs import Env


@dataclass
class Parser:
    url:             str             
    path_data:       str
    stop_categories: list[str]   
    tag_names:       list[str]

@dataclass
class Config:
    parser: Parser


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(
        parser =Parser(
            url=env('URL'),
            path_data=env('PATH_DATA'),
            stop_categories=list(env.list('STOP_CATEGORIES')),
            tag_names=list(env.list('TAG_NAMES'))
        )
    )