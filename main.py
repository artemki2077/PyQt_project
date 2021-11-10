from sqlalchemy import create_engine, MetaData, Table, Integer, String, \
    Column, DateTime, ForeignKey, insert, select, update, or_, and_
from datetime import datetime
from hashlib import sha256
import sys
import csv
from PyQt5.QtWidgets import QLineEdit, QWidget, QApplication, QPushButton, \
    QLabel, QTableWidget, \
    QTableWidgetItem, QFileDialog

# импортирования библиотек

metadata = MetaData()

engine = create_engine(
    "postgresql+psycopg2://egerxqhtcwcnti:c2de0ab971d2e36317f9ab03d097191edd79d154f032d86efdce83e6f56232b7@ec2-52-208"
    "-221-89.eu-west-1.compute.amazonaws.com:5432/dagdtfhhmkkc6u")  # подключение к бд

# Ниже объекты для управления базой данных и каждый отвечает за свою таблицу

Accounts = Table("Accounts", metadata,
                 Column('id', Integer(), primary_key=True),
                 Column('balance', Integer(), nullable=False),
                 )

Users = Table("Users", metadata,
              Column('id', Integer(), primary_key=True),
              Column('login', String(100), unique=True, nullable=False),
              Column("password", String(100), nullable=False),
              Column("account_id", Integer(), ForeignKey('Accounts.id'),
                     nullable=False),
              )

Transactions = Table("Transactions", metadata,
                     Column("id", Integer(), primary_key=True),
                     Column("account_id_from", Integer(),
                            ForeignKey('Accounts.id'),
                            nullable=False),
                     Column("account_id_to", Integer(),
                            ForeignKey('Accounts.id'),
                            nullable=False),
                     Column("amount", Integer(),
                            nullable=False),
                     Column("comment", String(100)),
                     Column("time", DateTime(), default=datetime.now)
                     )

Projects = Table("Projects", metadata,
                 Column('id', Integer(), primary_key=True),
                 Column('name', String(100), unique=True, nullable=False),
                 Column("password", String(100), nullable=False),
                 Column("User", Integer(), ForeignKey('Users.id'), unique=True, nullable=False),
                 Column("account_id", Integer(), ForeignKey('Accounts.id'),
                        nullable=False),
                 )

metadata.create_all(engine)

print("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


def chek_translate(username, username_to):
    # функция проверки перед транзакцией
    conn = engine.connect()
    r = conn.execute(select([Users]).where(
        or_(Users.c.login == username, Users.c.login == username_to)))
    return not not r.rowcount


def save_transaction(username_from, username_to, amount, comment, is_project):
    # функция сохранения транзакции
    # try:
    conn = engine.connect()
    r = conn.execute(select(Users.c.account_id).where(
        Users.c.login == username_from
    )) if not is_project else conn.execute(select(Projects.c.account_id).where(
        Projects.c.name == username_from
    ))
    account_id_from = r.first()[0]
    r = conn.execute(select(Users.c.account_id).where(
        Users.c.login == username_to
    ))
    account_id_to = r.first()[0]
    conn.execute(insert(Transactions).values(
        account_id_from=account_id_from,
        account_id_to=account_id_to,
        amount=int(amount),
        comment=comment if comment else None
    ))
    return True
    # except:
    #     return False


def take_money(username, amount, is_project):
    # функция отнимающая деньги
    if amount.isnumeric():
        amount = int(amount)
        conn = engine.connect()
        r = conn.execute(select([Projects]).where(Projects.c.name == username)) if is_project else conn.execute(
            select([Users]).where(Users.c.login == username))
        user = r.first()
        if user:
            r = conn.execute(
                select([Accounts]).where(Accounts.c.id == user[-1]))
            balance = r.first()[-1]
            if balance < amount:
                return False, "не хватает средств"
            else:
                conn.execute(
                    update(Accounts).where(Accounts.c.id == user[-1]).values(
                        balance=balance - amount
                    ))
                return True, "Успех"
        else:
            return False, "нет такого пользователя"
    else:
        return False, "некоректно набрана сумма"


def add_money(username, amount):
    # функция добавления денег
    amount = int(amount)
    conn = engine.connect()
    r = conn.execute(select([Users]).where(Users.c.login == username))
    user = r.first()
    if user:
        r = conn.execute(select([Accounts]).where(Accounts.c.id == user[-1]))
        balance = r.first()[-1]
        conn.execute(update(Accounts).where(Accounts.c.id == user[-1]).values(
            balance=balance + amount
        ))
        return True, "Успех"
    else:
        return False, "нет такого пользователя"


class SingUp(QWidget):
    # виджет регистрации
    def __init__(self):
        super(SingUp, self).__init__()
        self.resize(500, 400)
        self.setWindowTitle("Регистрация")
        self.login = QPushButton("LogIn?", self)
        self.login.resize(100, 35)
        self.login.clicked.connect(self.go_login)
        self.Label_username = QLabel("Username", self)
        self.Label_username.move(222, 100)
        self.username = QLineEdit(self)
        self.username.move(150, 130)
        self.username.resize(200, 25)
        self.Label_password = QLabel("Password", self)
        self.Label_password.move(222, 170)
        self.password = QLineEdit(self)
        self.password.move(150, 200)
        self.password.resize(200, 25)
        self.password.setEchoMode(QLineEdit.Password)
        self.singup = QPushButton("SingUp", self)
        self.singup.clicked.connect(self.go_singup)
        self.singup.move(200, 250)
        self.singup.resize(100, 35)
        self.error = QLabel("", self)
        self.error.move(200, 300)
        self.error.resize(300, 30)
        self.error.setStyleSheet("color: red")
        self.out_login = True  # переменая чтообы pep8 не ругался

    def go_singup(self):
        # регистрация
        conn = engine.connect()

        s = select([Users]).where(
            Users.c.login == self.username.text()
        )
        r = conn.execute(s)
        if not r.first():
            ins = insert(Accounts).values(balance=0)
            r = conn.execute(ins)
            account_id = r.inserted_primary_key[0]
            ins = insert(Users).values(login=self.username.text(),
                                       password=str(sha256(self.password.text()
                                                           .encode('utf-8'))
                                                    .hexdigest()),
                                       account_id=account_id)
            conn.execute(ins)
            self.go_login()
        else:
            self.error.setText("такое имя уже используется")

    def go_login(self):
        # переход в виджет входа
        self.hide()
        self.out_login = LogIn()
        self.out_login.show()


class CreatProj(QWidget):
    # виджет регистрации
    def __init__(self, username, account_id):
        super(CreatProj, self).__init__()
        self.resize(500, 400)
        self.setWindowTitle("Создание пректа")
        self.account_id = account_id
        self.username = username
        self.back = QPushButton("Back", self)
        self.back.resize(100, 35)
        self.back.clicked.connect(self.go_back)
        self.Label_name = QLabel("Project name", self)
        self.Label_name.move(222, 100)
        self.pr_name = QLineEdit(self)
        self.pr_name.move(150, 130)
        self.pr_name.resize(200, 25)
        self.Label_password = QLabel("Password", self)
        self.Label_password.move(222, 170)
        self.password = QLineEdit(self)
        self.password.move(150, 200)
        self.password.resize(200, 25)
        self.password.setEchoMode(QLineEdit.Password)
        self.make = QPushButton("Make", self)
        self.make.clicked.connect(self.go_make)
        self.make.move(200, 250)
        self.make.resize(100, 35)
        self.error = QLabel("", self)
        self.error.move(200, 300)
        self.error.resize(300, 30)
        self.error.setStyleSheet("color: red")
        self.out_login = True  # переменая чтообы pep8 не ругался
        self.out_main = True  # переменая чтообы pep8 не ругался

    def go_make(self):
        # регистрация
        conn = engine.connect()

        s = select([Users]).where(
            Users.c.login == self.pr_name.text()
        )
        r = conn.execute(s)
        if not r.first():
            ins = insert(Accounts).values(balance=0)
            r = conn.execute(ins)
            account_id = r.inserted_primary_key[0]
            ins = insert(Projects).values(name=self.pr_name.text(),
                                          password=str(sha256(self.password.text()
                                                              .encode('utf-8'))
                                                       .hexdigest()),
                                          User=self.account_id,
                                          account_id=account_id)
            conn.execute(ins)
            self.hide()
            self.out_main = ProjPage(self.username, self.pr_name.text())
            self.out_main.show()
        else:
            self.error.setText("такое имя уже занято")

    def go_back(self):
        # переход в виджет входа
        self.hide()
        self.out_login = MainPages()
        self.out_login.show()


class LogIn(QWidget):
    # виджет входа
    def __init__(self):
        super(LogIn, self).__init__()
        self.resize(500, 400)
        self.setWindowTitle("Вход")
        self.singup = QPushButton("SingUp?", self)
        self.singup.resize(100, 35)
        self.singup.clicked.connect(self.go_singup)
        self.Label_username = QLabel("Username", self)
        self.Label_username.move(222, 100)
        self.username = QLineEdit(self)
        self.username.move(150, 130)
        self.username.resize(200, 25)
        self.Label_password = QLabel("Password", self)
        self.Label_password.move(222, 170)
        self.password = QLineEdit(self)
        self.password.move(150, 200)
        self.password.resize(200, 25)
        self.password.setEchoMode(QLineEdit.Password)
        self.login = QPushButton("Login", self)
        self.login.move(200, 250)
        self.login.resize(100, 35)
        self.login.clicked.connect(self.go_login)
        self.error = QLabel("", self)
        self.error.move(200, 300)
        self.error.resize(300, 30)
        self.error.setStyleSheet("color: red")
        self.out_singUp = True  # переменая чтообы pep8 не ругался
        self.out_main_pages = True  # переменая чтообы pep8 не ругался

    def go_login(self):
        # входcc
        conn = engine.connect()
        s = select([Users]).where(
            and_(Users.c.login == self.username.text(),
                 Users.c.password == sha256(
                     self.password.text().encode("utf-8")).hexdigest())
        )
        r = conn.execute(s)
        if r.first():
            self.hide()
            self.out_main_pages = MainPages(self.username.text())
            self.out_main_pages.show()
        else:
            self.error.setText("неправильный логин или пароль")

    def go_singup(self):
        # переход в регистрацию
        self.hide()
        self.out_singUp = SingUp()
        self.out_singUp.show()


class SendMoney(QWidget):
    # виджет отправки денег
    def __init__(self, username, is_project, pr_name):
        super(SendMoney, self).__init__()
        self.setWindowTitle("Отправка денег")
        self.resize(500, 500)
        self.username = username
        self.pr_name = pr_name
        self.is_project = is_project

        self.back = QPushButton("назад", self)
        self.back.clicked.connect(self.go_back)

        self.send_to = QLabel("Кому:", self)
        self.send_to.move(75, 50)
        self.send_to.setStyleSheet("font-size: 35px")

        self.name_for = QLineEdit(self)
        self.name_for.move(280, 60)
        self.name_for.resize(180, 50)
        self.name_for.setStyleSheet("font-size: 35px")

        self.lable_amount = QLabel("Сколько:", self)
        self.lable_amount.move(75, 150)
        self.lable_amount.setStyleSheet("font-size: 35px")

        self.amount = QLineEdit(self)
        self.amount.move(280, 150)
        self.amount.resize(180, 50)
        self.amount.setStyleSheet("font-size: 35px")

        self.lable_comment = QLabel("Комент:", self)
        self.lable_comment.move(75, 240)
        self.lable_comment.setStyleSheet("font-size: 35px")

        self.comment = QLineEdit(self)
        self.comment.move(280, 240)
        self.comment.resize(180, 50)
        self.comment.setStyleSheet("font-size: 35px")

        self.send = QPushButton("Отправить", self)
        self.send.move(200, 350)
        self.send.resize(100, 40)
        self.send.clicked.connect(self.send_money)

        self.error = QLabel(self)
        self.error.move(200, 400)
        self.error.resize(300, 30)
        self.error.setStyleSheet("color: red")

        self.out_back = True  # переменая чтообы pep8 не ругался

    def send_money(self):
        # отправка денег и проверка перед этим
        ok = chek_translate(self.username, self.name_for.text())
        if ok:
            ok, message = take_money(self.username if not self.is_project else self.pr_name, self.amount.text(),
                                     self.is_project)
            if not ok:
                self.error.setText(message)
            else:
                ok, message = add_money(self.name_for.text(),
                                        self.amount.text())
                if not ok:
                    self.error.setText(message)
                else:
                    if save_transaction(self.username if not self.is_project else self.pr_name, self.name_for.text(),
                                        self.amount.text(),
                                        self.comment.text(), self.is_project):
                        self.go_back()
                    else:
                        self.error.setText("проблема с сохранением транзакции")
        else:
            self.error.setText("нет такогоj пользователя")

    def go_back(self):
        # уход
        self.out_back = MainPages(self.username) if not self.is_project else ProjPage(self.username, self.pr_name)
        self.hide()
        self.out_back.show()


class ProjPage(QWidget):
    def __init__(self, username, project):
        super(ProjPage, self).__init__()
        self.setWindowTitle("Профиль проекта")
        self.resize(500, 500)
        self.back = QPushButton("Выход", self)
        self.back.clicked.connect(self.go_back)
        self.pr_name = project

        self.name = username
        self.project_name = QLabel(project.capitalize(), self)
        self.project_name.move(195, 50)
        self.project_name.setStyleSheet("font-size: 50px")
        conn = engine.connect()
        s = select([Projects]).where(Projects.c.name == self.pr_name)
        r = conn.execute(s)
        account_id = r.first()[-1]
        self.account_id = account_id
        s = select([Accounts]).where(Accounts.c.id == account_id)
        r = conn.execute(s)
        balance = r.first()[-1]
        self.balance = QLabel(str(balance), self)
        self.balance.move(230, 130)
        self.balance.setStyleSheet("font-size: 25px")

        self.send_money = QPushButton("Отправить", self)
        self.send_money.move(280, 250)
        self.send_money.resize(200, 70)
        self.send_money.clicked.connect(self.go_send)

        self.transactions = QPushButton("транзакции Проекта", self)
        self.transactions.move(20, 250)
        self.transactions.resize(200, 70)
        self.transactions.clicked.connect(self.go_transactions)
        self.out_back = True  # переменая чтообы pep8 не ругался
        self.out_send = True  # переменая чтообы pep8 не ругался
        self.out_transactions = True  # переменая чтообы pep8 не ругался

    def go_send(self):
        # переход в виджет отправки денег
        self.out_send = SendMoney(self.name, True, self.pr_name)
        self.hide()
        self.out_send.show()

    def go_transactions(self):
        # переход в виджет отчёта транзакция
        self.out_transactions = MyTransactions(self.name, self.account_id, self.pr_name, True)
        self.hide()
        self.out_transactions.show()

    def go_back(self):
        # уход
        self.out_back = MainPages(self.name)
        self.hide()
        self.out_back.show()


class MainPages(QWidget):
    # виджет главной страницы
    def __init__(self, username):
        super(MainPages, self).__init__()
        self.setWindowTitle("Профиль")
        self.resize(500, 500)
        self.out_proj = True  # переменая чтообы pep8 не ругался
        self.out_creat_proj = True  # переменая чтообы pep8 не ругался
        self.back = QPushButton("Выход", self)
        self.back.clicked.connect(self.go_back)

        self.name = username
        self.usr = QLabel(self.name.capitalize(), self)
        self.usr.move(195, 50)
        self.usr.setStyleSheet("font-size: 50px")
        conn = engine.connect()
        s = select([Users]).where(Users.c.login == username)
        r = conn.execute(s)
        account_id = r.first()[-1]
        self.account_id = account_id
        s = select([Accounts]).where(Accounts.c.id == account_id)
        r = conn.execute(s)
        balance = r.first()[-1]
        self.balance = QLabel(str(balance), self)
        self.balance.move(230, 130)
        self.balance.setStyleSheet("font-size: 25px")

        self.send_money = QPushButton("Отправить", self)
        self.send_money.move(280, 250)
        self.send_money.resize(200, 70)
        self.send_money.clicked.connect(self.go_send)

        self.transactions = QPushButton("Мои транзакции", self)
        self.transactions.move(20, 250)
        self.transactions.resize(200, 70)
        self.transactions.clicked.connect(self.go_transactions)

        self.project = QPushButton("Проект", self)
        self.project.move(150, 350)
        self.project.resize(200, 70)
        self.project.clicked.connect(self.go_project)

        self.out_send = True  # переменая чтообы pep8 не ругался
        self.out_transactions = True  # переменая чтообы pep8 не ругался
        self.out_back = True  # переменая чтообы pep8 не ругался

    def go_project(self):
        conn = engine.connect()
        r = conn.execute(select([Projects]).where(
            Projects.c.User == self.account_id
        ))
        project_r = r.first()
        if project_r:
            self.out_proj = ProjPage(self.name, project_r[1])
            self.hide()
            self.out_proj.show()
        else:
            self.out_creat_proj = CreatProj(self.name, self.account_id)
            self.hide()
            self.out_creat_proj.show()

    def go_send(self):
        # переход в виджет отправки денег
        self.out_send = SendMoney(self.name, False, None)
        self.hide()
        self.out_send.show()

    def go_transactions(self):
        # переход в виджет отчёта транзакция
        self.out_transactions = MyTransactions(self.name, self.account_id, self.name, False)
        self.hide()
        self.out_transactions.show()

    def go_back(self):
        # уход
        self.out_back = LogIn()
        self.hide()
        self.out_back.show()


class MyTransactions(QWidget):
    # виджет всех транзакций
    def __init__(self, username, account_id, pr_name, is_project):
        super(MyTransactions, self).__init__()
        self.setWindowTitle("Мои транзакции")
        self.username = username
        self.proj_names = pr_name
        self.is_project = is_project
        self.resize(500, 550)
        conn = engine.connect()
        r = conn.execute(
            select([Transactions.c.account_id_to,
                    Transactions.c.account_id_from]).where(
                or_(Transactions.c.account_id_from == account_id,
                    Transactions.c.account_id_to == account_id)))
        users_account_id = list(
            set([item for sublist in r.fetchall() for item in sublist]))
        r = conn.execute(
            select([Users.c.account_id, Users.c.login]).where(
                Users.c.account_id.in_(users_account_id)))
        accounts_id_name = r.fetchall()
        r = conn.execute(
            select([Projects.c.account_id, Projects.c.name]).where(
                Users.c.account_id.in_(users_account_id))
        )
        accounts_id_proj = r.fetchall()

        self.names = {accounts_id_name[i][0]: accounts_id_name[i][1] for i in
                      range(0, len(accounts_id_name), 1)}
        self.pr_names = {accounts_id_proj[i][0]: accounts_id_proj[i][1] for i in
                         range(0, len(accounts_id_proj), 1)}
        self.names.update(self.pr_names)
        r = conn.execute(
            select(
                [Transactions.c.account_id_from, Transactions.c.account_id_to,
                 Transactions.c.amount, Transactions.c.comment,
                 Transactions.c.time]).where(
                or_(Transactions.c.account_id_from == account_id,
                    Transactions.c.account_id_to == account_id)))
        self.all_transactions = r.fetchall()
        self.table = QTableWidget(self)
        self.table.resize(500, 460)
        self.table.move(0, 40)
        self.table.setColumnCount(5)
        self.table.setRowCount(len(self.all_transactions))
        self.table.setHorizontalHeaderLabels(
            ["Кто", "Куда", "Сколько", "Комент", "Когда"])
        for n, i in enumerate(self.all_transactions):
            self.table.setItem(n, 0, QTableWidgetItem(self.names[i[0]]))
            self.table.setItem(n, 1, QTableWidgetItem(self.names[i[1]]))
            self.table.setItem(n, 2, QTableWidgetItem(str(i[2])))
            self.table.setItem(n, 3, QTableWidgetItem(i[3]))
            self.table.setItem(n, 4, QTableWidgetItem(str(i[4])))
        self.back = QPushButton("назад", self)
        self.back.clicked.connect(self.go_back)
        self.get_csv = QPushButton("получить в csv", self)
        self.get_csv.move(180, 0)
        self.get_csv.clicked.connect(self.csv)
        self.error = QLabel("", self)
        self.error.move(0, 500)
        self.error.resize(500, 50)
        self.error.setStyleSheet("color: red")
        self.out_back = True  # переменая чтообы pep8 не ругался

    def csv(self):
        # выгрузка в файл
        try:
            filename, ok = QFileDialog.getSaveFileName(self,
                                                       "Сохранить файл",
                                                       ".csv", )
            if filename.split(".")[-1] != "csv":
                raise FileNotFoundError("неправильно введён название")
            with open(filename, "w", newline='') as csv_file:
                writer = csv.writer(csv_file, delimiter=',')
                for i in self.all_transactions:
                    writer.writerow(
                        [self.names[i[0]], self.names[i[1]], str(i[2]), i[3],
                         str(i[4])])
        except FileNotFoundError as e:
            self.error.setStyleSheet("color: red")
            self.error.setText(str(e))
        else:
            self.error.setStyleSheet("color: green")
            self.error.setText("успешно сохранено в " + filename)

    def go_back(self):
        # уход
        self.out_back = ProjPage(self.username, self.proj_names) if self.is_project else MainPages(self.username)
        self.hide()
        self.out_back.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = LogIn()
    # form = MainPages("artem")
    form.show()
    sys.exit(app.exec())
