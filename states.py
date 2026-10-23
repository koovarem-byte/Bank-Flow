from aiogram.fsm.state import State, StatesGroup


class PersonalLinkForm(StatesGroup):
    fio = State()
    email = State()
    phone = State()

class AdminLinkForm(StatesGroup):
    link = State()

class BusinessQuestionForm(StatesGroup):
    question = State()

class VtbCallForm(StatesGroup):
    time = State()
    phone = State()

class AdminBusinessAnswerForm(StatesGroup):
    answer = State()

class AdminCommentForm(StatesGroup):
    comment = State()

class AdminLinkCommentForm(StatesGroup):
    comment = State()

class WithdrawalForm(StatesGroup):
    amount = State()
    phone = State()
    bank = State()

class AdminUserForm(StatesGroup):
    value = State()
