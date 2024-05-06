# Gift_Recommendation_System
This is a gift recommendation system that, based on minimal input data, can recommend a gift for a person. This is a learning project. As a result, it is supposed to create a simple web page or telegram bot, where you can pick up a gift.

## Project Structure
```
.
├───config
│   └───params.yaml                        # configuration parameters
├───data
│   ├───raw                     
│   │   └───ozon_data.csv                  # csv file with all products
│   └───processed
│       ├───train.csv                      # dataset for training 
│       └───valid.csv                      # dataset for validation
├───src                         
│   └───parse.py                           # scrapes products from ozon.ru
├───bot
│   ├───config_data                     
│   │   └───config.py                      # configuration parameters for bot
│   ├───handlers
│   │   ├───admin_handlers.py              # handlers admin 
│   │   └───user_handlers.py               # handlers user
│   ├───keyboards                     
│   │   └───main_keyboards.py              # keyboards
│   ├───.env                               #
│   └───bot.py                             # 
├───.gitignore
├───requirements.txt                       # all required dependencies
├───Gift recommendation system.ipynb.ipynb # trains the model on the training dataset,
│                                            contains class with the tuned model,
│                                            example how the inference works
└───README.md
```
## How to use?
The device must have python and git. Commands are executed from the terminal.

1. Clone the repo — git clone https://github.com/tutsilianna/Gift_Recommendation_System;
2. Install all dependencies — pip install -r requirements.txt;
3. ...
