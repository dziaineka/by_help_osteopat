from aiogram.dispatcher.filters.state import State, StatesGroup


# FSM states
class Form(StatesGroup):
    initial = State()  # Will be represented in storage as 'Form:initial'
    good_man_name = State()
    name = State()  # Will be represented in storage as 'Form:name'
    age = State()  # Will be represented in storage as 'Form:age'
    injury_date = State()
    injury_list = State()
    location = State()
    communication = State()
    questions = State()
    approve = State()
