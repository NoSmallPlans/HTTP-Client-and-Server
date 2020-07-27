import sys
import os
import socket
import time
from time import gmtime, strftime


class ReqHeader:
    def __init__(self, str):
        self.raw_str = str
        self.header_map = {}
        self.method = None
        self.path = None
        self.error = False
        self.error_msg = ''
        delim = '\r\n'
        decoded = str.decode('utf-8')
        header_list = decoded.split(delim)
        methodPath = header_list.pop(0)
        methodPath = methodPath.split()
        self.method = methodPath[0]
        if self.method != 'GET':
            self.error = True
            self.error_msg = '501 NOT IMPLEMENTED'
        self.path = methodPath[1]
        self.sanitize_path(self.path)
        for row in header_list:
            row = row.split()
            key = row[0].rstrip(':')
            val = row[1]
            self.header_map[key] = val

    def sanitize_path(self, path):
        if '../' in path:
            self.error = True
            self.error_msg = '400 BAD REQUEST'

    def debug_print(self):
        print(self.method)
        print(self.path)
        print(self.header_map)


class ResHeader:
    def __init__(self, resource):
        self.header_map = {}
        self.protocol = 'HTTP/1.1'
        self.status = '200 OK'
        self.header_map['Connection'] = 'close' #default to close
        self.set_resource_data(resource)

    def set_resource_data(self, resource):
        if not resource.error:
            self.header_map['Content-Length'] = str(resource.content_length)
            self.header_map['Content-Type'] = resource.filetype
            self.header_map['Date'] = self.get_date()
            self.header_map['Last-Modified'] = str(resource.last_modified)

    def get_date(self):
        return strftime("%a, %d %b %Y %H:%M:%S GMT", gmtime())

    def to_b_string(self):
        delim = '\r\n'
        arnold = '\r\n'
        result = ''
        result += self.protocol + ' ' + self.status + delim
        for key in self.header_map:
            result += key + ': ' + self.header_map[key] + delim
        result += arnold
        return result.encode('utf-8')


class FileObj:
    def __init__(self, path):
        self.root = './web_root'
        self.error = False
        self.error_msg = ''
        self.path = self.root + path 
        self.set_metadata()

    def set_metadata(self):
        if os.path.isdir(self.path):
            if self.path.endswith('/'): 
                self.path = self.path + 'index.html'
            else:
                self.path = self.path + '/index.html'
        if os.path.exists(self.path):
            self.content_length = os.path.getsize(self.path)
            self.last_modified = self.format_file_time(os.path.getmtime(self.path))
            self.filetype = self.filetype_from_ext(os.path.splitext(self.path)[1])
        else:
            self.error_msg = '404 NOT FOUND'
            self.error = True

    def format_file_time(self, inputTime):
        return strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(inputTime))

    def send_bytes(self, buffer_size, socket):
        try:
            file = open(self.path,'rb')
            buffer = file.read(buffer_size)
        except OSError as msg:
            print('Error trying to read file')
        while len(buffer):
            try:
                socket.send(buffer)
            except OSError as msg:
                print('Error trying to send data')        
            try:
                buffer = file.read(buffer_size)
            except OSError as msg:
                print('Error trying to read file')
            

    def filetype_from_ext(self, ext):
        type_map = {}
        type_map['.txt'] = 'text/plain'
        type_map['.html'] = 'text/html'
        type_map['.htm'] = 'text/htm'
        type_map['.css'] = 'text/css'
        type_map['.jpg'] = 'image/jpeg'
        type_map['.jpeg'] = 'image/jpeg'
        type_map['.png'] = 'image/png'
        ext = ext.lower()
        if ext in type_map:
            return type_map[ext]
        else:
            self.error = True
            self.error_msg = '415 Unsupported Media Type'
            return 'err'

def try_send(connection, data, err_msg):
    try:    
        connection.send(data)
    except OSError as msg:
        print(err_msg)

def get_until_term_char(conn, bufferSize):
    terminating_str = b'\r\n\r\n'
    the_terminator = terminating_str
    arnold = the_terminator
    cumulative_data = b''
    data = None
    stopFlag = False
    while cumulative_data.find(arnold) == -1:
        try:    
            data = conn.recv(bufferSize)
        except OSError as msg:
            print('Error trying to get request header')        
        cumulative_data += data
    result = cumulative_data.split(arnold, 1)[0]
    return result;

if __name__ == "__main__":

    try:
        PORT = int(sys.argv[1])
    except:
        print('integer port number required as first and only parameter')
        sys.exit(1)

    HOST = ''
    BUFFER_SIZE = 1024
    
    try:
        s = socket.socket()
    except OSError as msg:
        s = None
    try:    
        s.bind((HOST, PORT))
        s.listen(1)
    except OSError as msg:
        s.close()
        s = None
    if s is None:
        print('Error trying to open socket')
        sys.exit(1)

    while True:
        connection, addr = s.accept()
        data = get_until_term_char(connection, BUFFER_SIZE)
        reqHeaders = ReqHeader(data)
        file = FileObj(reqHeaders.path)
        resHeaders = ResHeader(file)
        if reqHeaders.error:
            resHeaders.status = reqHeaders.error_msg
            try_send(connection,resHeaders.to_b_string(), 'Error trying to send response header')
            print(resHeaders.status)
            connection.close()
        elif file.error:
            resHeaders.status = file.error_msg
            try_send(connection,resHeaders.to_b_string(), 'Error trying to send response header')
            print(resHeaders.status)
            connection.close()
        else:
            try_send(connection,resHeaders.to_b_string(), 'Error trying to send response header')
            file.send_bytes(BUFFER_SIZE, connection)
            print(resHeaders.status)
            connection.close()



