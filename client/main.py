import sys
import os
import socket
import rsa
import time
import zlib
import random
import threading
import hashlib
import json
import jwt
from rich import print
from rich.console import Console
from rich.tree import Tree
from rich.align import Align

from anonfile import AnonFile

global buffer

# Vars
console = Console()
anon = AnonFile()
s = socket.socket()
buffer = 4096

"""
def cls:
    Clear terminal screen
"""
# Read config file
config_file = "config.json"
with open(config_file, "r") as f:
    config_json = json.load(f)
ip: str = config_json["ip"]
port: int = config_json["port"]

def cls():
    if os.name == 'nt':
        os.system('cls')

    else:
        os.system("clear")

class API:
    """
    class Chat:
        arg: private_key, public_key

        def send (message: str):
            Allows you to send an encrypted message to the server

        def recv (buffer: int):
            Receives a message from the encrypted server

    class Load_keys:
        arg: private_key, public_key

        def private:
            Load the private key

        def public:
            Load the public key

        def load_all:
            Load the private and public key
    """
    class Chat:
        def __init__(self, priv_key, pub_key) -> None:
            self.priv_key = priv_key
            self.pub_key = pub_key

        def send(self, msg: str):
            s.send(rsa.encrypt(msg.encode(), self.pub_key))

        def recv(self, buffer: int):
            msg = s.recv(buffer)
            return rsa.decrypt(msg, self.priv_key).decode()

    class Load_keys:
        def __init__(self, pub_key, priv_key) -> None:
            self.pub_key = pub_key
            self.priv_key = priv_key

        def private(self):
            return rsa.PrivateKey.load_pkcs1(self.priv_key)

        def public(self):
            return rsa.PublicKey.load_pkcs1(self.pub_key)

        def load_all(self):
            return rsa.PrivateKey.load_pkcs1(
                self.priv_key), rsa.PublicKey.load_pkcs1(self.pub_key)


class UI:
    """
    def random_color:
        It will take a random color and be entered as the username color

    def banner:
        The ASCII banner that will be centered

    def get_server:
        Get the server ip and port

    def get_username:
        Get the username from the input will send it to the server

    def run:
        Where the code will start
    """

    def __init__(self) -> None:
        pass

    def random_color(self):
        # Color list:
        # https://rich.readthedocs.io/en/stable/appendix/colors.html
        colors = [
            "red",
            "blue",
            "cyan",
            "yellow",
            "magenta",
            "green",
            "purple",
            "violet",
            "gold"]

        # Random choice from array
        color = random.choice(colors)
        return color

    def banner(self):
        print(Align(r"""[purple]
  _____  _____ ______ _____
 / ____|/ ____|  ____/ ____|
 | |    | (___ | |__ | |
 | |     \___ \|  __|| |
 | |____ ____) | |___| |____
 \_____|_____/|______\_____|
""", "center"))

    def get_server(self):
        global ip,port
        server_ip = ip
        #console.input("[b]Insert server address[/b] :laptop_computer: : ")

        server_port = int(port)
        #int(console.input("[b]Insert server port[/b] : "))

        # If server_ip == "local"... change server_ip to 127.0.0.1

        match server_ip:
            case "local" | "localhost" | "::1":
                server_ip = "127.0.0.1"

        return server_ip, server_port

    def get_username(self):
        username = console.input(
            "[b]Insert your username[/b] :ID: : ")

        # Random color set
        color = self.random_color()
        username_styled = f"<[{color}]{username}[/{color}]>"
        return username, username_styled

    def get_password(self):
        password = console.input("[b]Insert password[/b] :locked_with_key: : ")
        # Encrypt password
        return hashlib.md5(password.encode()).hexdigest()


    def start(self):
        self.banner()
        ip, port = self.get_server()
        username, username_styled = self.get_username()
        #password = self.get_password()
        return ip, port, username, username_styled


class Chat:
    """
    class chat_api: RSA custom socket

    var (str) username_syled: (<Username>) {
        It is the username but compliant for sending via socket
        making all the username available
    }

    var (str) username: Current username

    fun receive: Receive messages via socket
    fun write: Where the user will put the message, it will be encrypted
    fun run: Where the code will start
    """

    def __init__(self, chat_api, username_styled, username) -> None:
        self.chat_api = chat_api
        self.username_styled = username_styled
        self.username = username

    def help_cmd(self):
        docs = """
/help   show the command list
/nick   show your nickname
/upload upload your file
"""
        print(docs)

    def receive(self):
        while True:
            try:
                print(self.chat_api.recv(buffer))
            except rsa.pkcs1.DecryptionError:
                pass

    def write(self):
        try:
            while True:
                msg = input("")
                try:
                    msg_splited = msg.split()
                
                    # Remove line up
                    sys.stdout.write("\033[F")

                    if (len(msg_splited[0].strip()) > 0):
                            if msg_splited[0] == "/help":
                                self.help_cmd()
                            
                            elif msg_splited[0] == "/nick":
                                print(self.username)

                            elif msg_splited[0] == "/upload":
                                try:
                                    upload = anon.upload(msg_splited[1], progressbar=False)
                                    print("<[green][i]You[/i][/green]>" + " [b]Upload: [/b] " + str(upload.url.geturl()))
                                    self.chat_api.send(self.username_styled + " [b]Upload:[/b] " + str(upload.url.geturl()))
                                except IndexError:
                                    print("Usage: /upload <path>")
                                except FileNotFoundError:
                                    print("File not found")

                            elif not msg_splited[0].startswith("/"):
                                self.chat_api.send("{\"styled_username\":\""+self.username_styled+"\" ,\"message\":\"" + msg+"\", \"token\":\""+API.token+"\"}")
                                
                                print("<[green][i]You[/i][/green]> " + msg)
                except IndexError:
                    pass

        except KeyboardInterrupt:
            s.send("/exit".encode())
            sys.exit(1)

    def run(self):
        receive_process = threading.Thread(target=self.receive)
        receive_process.start()
        write_process = threading.Thread(target=self.write)
        write_process.start()


class Main:
    """
    def connect:
        It allows you to connect to the server, you will receive the RSA keys

    def send_username:
        Send yours username to server

    def get_buffer:
        Get from server buffer - RSA size and message size

    def get_welcome_message:
        Get welcome message from server

    def send_password:
        Send password for login on server 

    def run:
        Where the code will start
    """

    def __init__(self) -> None:
        pass

    def connect(self):
       
        ui = UI()    

        #Connection
        while True:
            try:
                s.connect((self.ip, self.port))
                break;
            except ConnectionRefusedError:
                cls()
                print("[red]ERROR[/red]: Connection refused")
                
        #==> Hello
        s.send(('{"username":"'+self.username+'","message":"Hello"}').encode())
        confirm = s.recv(1024).decode()
        if "/accepted" not in confirm:
            print("[red]ERROR[/red]: Login not Accepted by server")
            s.close()
            quit()
        print("[blue]INFO[/blue]: Hello message sent to server")
        #=========
        #==> RSA Key Exchange ========================================
        # Get buffer from server
        buffer = self.get_buffer()

        # Decompress keys with zlib
        public_key = zlib.decompress(s.recv(buffer))
        private_key = zlib.decompress(s.recv(buffer))

        # Key load
        client_key = API.Load_keys(public_key, private_key)
        self.private_key, self.public_key = client_key.load_all()
        # API
        self.chat_api = API.Chat(self.private_key, self.public_key)
        time.sleep(0.5)
        #==============================================================

        #==> Hello with nonce
        client_nonce = str(random.randint(0,sys.maxsize))
        payload = ('{"username":"'+self.username+'","nonce":"'+client_nonce+'"}')
        s.send(rsa.encrypt(payload.encode(),self.public_key))
        server_nonce = rsa.decrypt(s.recv(1024),self.private_key).decode()
        print("[blue]INFO[/blue]: Server nonce has been recieved")
        
        #=========   
        
        #self.username, self.username_styled, = ui.get_username()
        self.password = ui.get_password()
        # Send username to server and wait 0.5s
        self.send_login(self.username,self.password,client_nonce,server_nonce)
        console.print({"Token":API.token})
        





        # Welcome screen
        cls()
        self.get_welcome_message()
        
        
        chat = Chat(self.chat_api, self.username_styled, self.username)
        chat.run()

    def send_login(self, username: str,password: str,client_nonce: str, server_nonce: str):
        
        payload = ('{"username":"'+username+'","password":"'+str(hex(int(password,base=16)^int(client_nonce,base=16)^int(server_nonce,base=16)))+'"}').encode()
        s.send(rsa.encrypt(payload,self.public_key))
        # Confirm: /exit or /accepted
        confirm = rsa.decrypt(s.recv(1024),self.private_key).decode()
        if "/accepted " not in confirm:
            print("[red]ERROR[/red]: Login not Accepted by server")
            s.close()
            quit()
        else:
            API.token = confirm.split(" ")[1]
            
    def send_puzzle(self):
        temp = 0
        temphash = ""
        challenge = self.get_buffer(self)
        while 1:
            temphash = hashlib.sha256(challenge.encode() + str(temp).encode()).hexdigest()
            #print(str(temp).encode())
            #print(temphash[len(temphash) - 10:])
            if(temphash[len(temphash) - 5:] == "00000"):
                break
            temp = temp + 1
            #if(temp%10000 == 0):
                #print("asd")
        print(temphash)
        s.send(temphash.encode())

    def send_password(self, password: str):
        s.send(password.encode())
        confirm = s.recv(1024).decode()
        # Confirm: /exit or /accepted
        if confirm != "/accepted":
            print("[red]ERROR[/red]: Incorrect password")
            s.close()
            quit()

    def get_buffer(self):
        return int(s.recv(buffer).decode())

    def get_welcome_message(self):
        print(Align(self.chat_api.recv(buffer), "center"))

    def run(self):
        ui = UI()
        self.ip, self.port, self.username, self.username_styled = ui.start()
        self.connect()

if __name__ == "__main__":
    main = Main()
    main.run()
