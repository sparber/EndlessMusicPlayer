import socket
import ssl
import select
import time
import sys



class TheServer:
    def __init__(self, host, port):
        self.inputA_list = []
        self.inputB_list = []
    
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(200)

    def main_loop(self):
        ss = select.select
        while True:
            sockets = [self.server]+self.inputA_list+[x for x in self.inputB_list if x != None]
            inputready, outputready, exceptready = ss(sockets, [], [])
            
            for sock in inputready:
                if sock == self.server:
                    clientsock, clientaddr = self.server.accept()
                    print clientaddr, "has connected"
                    self.inputA_list.append(clientsock)
                    self.inputB_list.append(None)
                    
                    continue
                
                if sock in self.inputA_list:
                    try:
                        data = sock.recv(2**14)
                    except socket.error:
                        data = ""
                    
                    index = self.inputA_list.index(sock)
                    
                    if len(data) == 0:
                        self.disconnect(index)
                        break

                    if self.inputB_list[index] != None:
                        print "receiving unwanted data"
                    else:
                        ssl_sock = self.create_connection(data)
                        if ssl_sock == None:
                            self.disconnect(index)
                            break
                            
                        self.inputB_list[index] = ssl_sock
                    break
                    
                else:
                    
                    data = self.read_SSL_socket(sock)
                    if data == None:
                        continue
                    
                    index = self.inputB_list.index(sock)
                    
                    if len(data) == 0:
                        self.disconnect(index)
                        break
                    
                    try:
                        self.inputA_list[index].sendall(data)
                    except socket.error:
                        self.disconnect(index)
                        break
                        
    
    def disconnect(self, index):
        sockA = self.inputA_list[index]
        sockB = self.inputB_list[index]
        
        if sockA != None:
            sockA.close()
        if sockB != None:
            sockB.close()
        
        del self.inputA_list[index]
        del self.inputB_list[index]
        
    
    def read_SSL_socket(self, sock):
        try:
            data = sock.recv(1024)
        except ssl.SSLError as e:
            # Ignore the SSL equivalent of EWOULDBLOCK, but re-raise other errors
            if e.errno != ssl.SSL_ERROR_WANT_READ:
                raise
            return None
        except socket.error:
            return ""
        
        data_left = sock.pending()
        while data_left:
            try:
                data += sock.recv(data_left)
            except socket.error:
                return ""
            data_left = sock.pending()
        
        return data
        
    
    def create_connection(self, data):
        
        try:
            host, url, http_version, headers = self.extract_info(data)
        except ValueError:
            return None
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = ssl.wrap_socket(s)
        
        sock.connect((host, 443))
        
        sock.setblocking(0)
        
        sock.write("GET %s HTTP/%s\n" % (url, http_version))
        for name, value in headers:
            sock.write("%s: %s\n" % (name, value))
        sock.write("\n")
        
        return sock


    def extract_info(self, data):
        
        lines = data.splitlines()
        
        if not lines[0].startswith("GET"):
            raise ValueError("unsupported request type")
        
        end = lines[0].find(" HTTP/1.")
        url = lines[0][5:end]
        http_version = lines[0][end+6:]
        
        if not url.startswith("https://"):
            raise ValueError("nothing to forward")
        host = url[8:]
        end = host.find("/")
        
        url = host[end:]
        host = host[:end]
        
        headers = []
        for line in lines[1:]:
            if not line:
                break
            
            name, value = line.split(": ", 1)
            if name == "Host":
                value = host
            headers.append((name, value))
        
        return host, url, http_version, headers



if __name__ == '__main__':
    server = TheServer('', 9090)
    try:
        server.main_loop()
    except KeyboardInterrupt:
        print "Ctrl C - Stopping server"
        sys.exit(1)


