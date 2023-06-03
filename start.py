import time, random, os, re, unicodedata

from colorama import just_fix_windows_console, Fore, Back, Style
from datetime import datetime
from telethon.sync import TelegramClient
from telethon.errors.rpcerrorlist import PeerFloodError, SessionPasswordNeededError, PasswordHashInvalidError, PhoneCodeInvalidError, PhoneNumberBannedError

api_id = 21009513
api_hash = '1e51d89e972bd90ccac0786a683204a1'

def clearConsole():
    os.system('cls' if os.name=='nt' else 'clear')

class TGSpam:
    def __init__(self):
        self.api_id = api_id
        self.api_hash = api_hash
        self.accounts = self.readAccounts()

        self.logToFile("НАЧАЛО РАБОТЫ СКРИПТА\n\n")
        self.connect()
        self.users = self.scrapeMembers(self.selectChat())
        random.shuffle(self.users)
        self.spamMessages = self.getSpamMessages()
        random.shuffle(self.getSpamMessages())
        self.spam(self.users, self.spamMessages)

    def readAccounts(self):
        accounts = []
        with open('TGAccounts.txt', 'r') as file:
            for line in file:
                phone_number = line.strip()
                account = {'phone': phone_number}
                accounts.append(account)
        return accounts

    def logToFile(self, text):
        with open("TGSpam.log", 'a') as file:
            if "\n---\n" != text:
                date_time = datetime.now().strftime("[%Y.%m.%d %H:%M:%S]")
                file.write(f"{date_time} {text} \n")
            else:
                file.write(f"{text} \n")

    def logMessageInfo(self, text):
        print(Style.RESET_ALL + Style.BRIGHT + Fore.CYAN + text + Style.RESET_ALL)
        self.logToFile(text)

    def logMessageError(self, text):
        print(Style.RESET_ALL + Style.BRIGHT + Fore.RED + text + Style.RESET_ALL)
        self.logToFile(text)

    def logMessageWarning(self, text):
        print(Style.RESET_ALL + Style.BRIGHT + Fore.YELLOW + text + Style.RESET_ALL)
        self.logToFile(text)

    def logInput(self, text):
        return input(Style.RESET_ALL + Style.BRIGHT + Fore.GREEN + text + Style.RESET_ALL)
        self.logToFile(text)

    def сleanBadSymbols(self, txt):
        cleaned_name = re.sub(r'[<>:"/\\|?*]', '', txt)
        cleaned_name = ''.join(c for c in cleaned_name if unicodedata.category(c) != 'So')
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
        return cleaned_name

    def checkAccount(self, account):
        try:
            account['tgClient'].send_message("SpamBot", "/start")
            time.sleep(1)
            lastMessageFromBot = account['tgClient'].get_messages("SpamBot", limit=1)[0].message
            if lastMessageFromBot == "Good news, no limits are currently applied to your account. You’re free as a bird!" or lastMessageFromBot == "Ваш аккаунт свободен от каких-либо ограничений.":
                account['status'] = True;
                return True
            else:
                self.logMessageError(f"[{account['phone']}] Аккаунт ограничен.")
                account['status'] = False;
                return False
        except PeerFloodError:
            self.logMessageError(f"[{account['phone']}] Аккаунт ограничен.")
            account['status'] = False;
            return False

    def checkVerificationCode(self, account):
        try:
            account['tgClient'].sign_in(account['phone'], self.logInput('Введите верификационый код: '))
        except PhoneCodeInvalidError:
            self.logMessageError(f"[{account['phone']}] Верификационый код не правильный.")
            self.checkVerificationCode(account)
        except SessionPasswordNeededError:
            self.check2FPassword(account)

    def check2FPassword(self, account):
        try:
            account['tgClient'].sign_in(password = self.logInput('Введите двуфакторный пароль: '))
        except PasswordHashInvalidError:
            self.logMessageError(f"[{account['phone']}] Двухфакторный пароль не правильный.")
            self.check2FPassword(account)


    def connect(self):
        for account in self.accounts:
            account['tgClient'] = TelegramClient(account['phone'], self.api_id, self.api_hash)
            account['exceptionsInARow'] = [];
            account['onPauseUntil'] = 0;
            account['status'] = True;
            account['tgClient'].connect()
            self.logMessageInfo(f"Подключения аккаунта с номером: {account['phone']}...")
            if not account['tgClient'].is_user_authorized():
                try:
                    account['tgClient'].send_code_request(account['phone'])
                except PhoneNumberBannedError:
                    self.logMessageError(f"[{account['phone']}] Аккаунт заблокирован")
                    account['status'] = False
                    self.logMessageInfo("\n---\n")
                    continue
                self.checkVerificationCode(account)

            if self.checkAccount(account):
                self.logMessageInfo(f"[{account['phone']}] Аккаунт не имеет ограничений.")
                self.logMessageInfo("\n---\n")
            else:
                self.logMessageInfo("\n---\n")
            account['tgClient'].disconnect()

    def selectChat(self):
        clearConsole()
        self.accounts[0]['tgClient'].connect()
        groups = [dialog for dialog in self.accounts[0]['tgClient'].get_dialogs() if dialog.is_group and dialog.is_channel and dialog.entity.username]
        self.accounts[0]['tgClient'].disconnect()
        self.logMessageInfo('C какого чата вы бы хотели спарсить участников, что бы сразу начать на них рассылку:\n')
        [self.logMessageWarning(str(groups.index(group) + 1) + '. ' + self.сleanBadSymbols(group.title)) for group in groups]
        return self.selectChatInput(groups)
    
    def selectChatInput(self, groups):
        try:
            selectedChatIndex = int(self.logInput('\n\nВведите индекс чата подлежащий рассылки участникам выбранного чата: '))
            selectedDialogObject = groups[int(selectedChatIndex) - 1]
            return selectedDialogObject.entity.username
        except ValueError:
            self.logMessageError("Пожайлуста введите число, а не строку.")
            self.selectChatInput(groups)

    def scrapeMembers(self, selectedGroup):
        clearConsole()
        users = []
        for account in self.accounts:
            if account['status'] == True:
                self.logMessageWarning(f"[{account['phone']}] Парсит участников...")
                account['tgClient'].connect()
                for user in account['tgClient'].get_participants(selectedGroup, aggressive=False):
                    if self.accounts.index(account) == 0:
                        if user.username:
                            users.append(user.username);
                        else:
                            users.append(user.id);
                account['tgClient'].disconnect()
        self.logMessageInfo(f"\nПолучено {len(users)} участников!")
        self.logMessageInfo(f"Начинаем атаку")
        return users

    def getSpamMessages(self):
        with open("TGSpamText.txt", 'r', encoding='utf-8') as file:
            text = file.read()
        elements = text.split("\n^^^")
        return elements

    def selectAccount(self):
        workAccounts = []
        for account in self.accounts:
            if account['status'] == True and account['onPauseUntil'] <= int(time.time()):
                workAccounts.append(account);
        selectedAccount = random.choice(workAccounts)
        return selectedAccount;

    def setException(self, phone, exceptIsset):
        for account in self.accounts:
            if account['phone'] == phone:
                if(len(account['exceptionsInARow']) > 5):
                    account['exceptionsInARow'].pop(0);
                account['exceptionsInARow'].append(exceptIsset)
                if(account['exceptionsInARow'].count(True) == 6):
                    if self.checkAccount(account) == False:
                        account['exceptionsInARow'] = [];
                    else:
                        account['exceptionsInARow'] = [];
                        account['onPauseUntil'] = int(time.time()) + 120;

    def spam(self, users, messages, delay=15):
        clearConsole()
        self.logMessageWarning(f"Начало атаки!\n\n")
        for user in users:
            time.sleep(delay)
            account = self.selectAccount();
            message = random.choice(messages)
            if account:
                account['tgClient'].connect();
                try:
                    self.logMessageWarning(f"[{account['phone']}] Попытка отправить сообщения пользователю {user}")
                    account['tgClient'].send_message(user, message)
                except PeerFloodError:
                    if self.checkAccount(account['tgClient']) == True:
                        self.logMessageError(f"[{account['phone']}] Флуд ошибка ставим паузу 120 сек.")
                        account['onPauseUntil'] = int(time.time()) + 120;
                    else:
                        self.logMessageError(f"[{account['phone']}] Аккаунт заблокирован.")
                except Exception as e:
                    self.logMessageError(f"[{account['phone']}] Неизвестная ошибка")
                    self.setException(account['phone'], True)
                    continue
                else:
                    if user != users[-1]:
                        self.logMessageInfo(f"[{account['phone']}] Сообщения отправленно")
                        self.setException(account['phone'], False)
                        #account['tgClient'].delete_dialog(user)
                account['tgClient'].disconnect();
            else:
                self.logMessageError("Все аккаунты заблокированны")


just_fix_windows_console();
TGSpam()