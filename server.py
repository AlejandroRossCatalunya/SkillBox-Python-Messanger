"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)
        if self.login is None:
            if decoded.startswith("login:"):
                # Домашняя работа: проверка введённого логина на уникальность
                current_login = decoded.replace("login:", "").replace("\r\n", "")
                if current_login not in [cl.login for cl in self.server.clients]:
                    self.login = decoded.replace("login:", "").replace("\r\n", "")
                    self.transport.write(f"Привет, {self.login}!\r\n".encode())
                    # Отправка истории сообщения при успешной авторизации
                    self.send_history()
                else:
                    self.transport.write(f"Логин {current_login} занят, попробуйте другой!".encode())
                    self.transport.close()  # Отключение клиента от сервера
        else:
            self.send_message(decoded)
            # Домашняя работа: добавление сообщения в историю чата
            if decoded != "\r\n":
                # Вызов функции, добавляющей сообщение в историю
                self.change_history(decoded)

    def send_history(self):
        '''
        Функция отправляет подключившемуся пользователю историю сообщений.
        :return: void
        '''
        if len(self.server.history) > 0:
            for message in self.server.history:
                self.transport.write(message.encode())

        '''
        Если история сообщений не будет очищаться, то функция будет выглядеть следующим образом:
        if len(self.server.history) > 0:
            for message in self.server.history[-10:]:
                self.transport.write(message.encode())
        '''

    def change_history(self, message):
        '''
        Функция добавляет входящее сообщение в историю чата.
        Если в истории уже содержится 10 сообщений, то удаляет самое старое из них.
        :param message: входящее непустое сообщение от пользователя
        :return: void
        '''
        self.server.history.append(f"<{self.login}> {message}\r\n")
        if len(self.server.history) > 10:
            del self.server.history[0]

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    history: list   # Для домашней работы: список последних 10 сообщений чата

    def __init__(self):
        self.clients = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8000
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
