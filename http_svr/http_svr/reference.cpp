#include <cstdio>
#include <iostream>
#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <unistd.h>
#include <algorithm>
#include <cstring>
#include <unistd.h>

using namespace std;


void sock_send(int sockid, string text_str);

string sock_receive(int sockid, sockaddr_in * cli_sock_addr, char* buffer, int bufferSize) {
    string term_str = "\r\n\r\n";
    string received_str;
    int cli_addrlen = sizeof(cli_sock_addr);
    while (received_str.find(term_str)  == std::string::npos) {
        memset(buffer, 0, bufferSize);
        ssize_t received = recvfrom(sockid, buffer, bufferSize
            ,0, (struct sockaddr*) & cli_sock_addr, (socklen_t*)&cli_addrlen);

        if (received == -1) {
            sock_send(sockid, "Server error during receipt of message");
            perror("Error during receive");
            exit(1);
        } else  {
            string s(buffer);
            received_str += s;
        }
    }
    received_str.resize(received_str.size()-4);
    return received_str;
}

void sock_send(int sockid, string text_str) {
    if(text_str.size() < 1 || text_str.size() > 131072) {
        sock_send(sockid, "Error: server attempted to send message of invalid length");
        return;
    }

    string term_str = "\r\n\r\n";
    string output = text_str + term_str;
    int msgSize = output.length();
    ssize_t sent = 0;
    while(sent < msgSize) {
        sent+= send(sockid, &output.c_str()[sent], output.length()-sent, 0);
        if (sent == -1) {
            perror("Error during send response");
            exit(1);
        }
    }
}


int main(int argc, char* argv[])
{
    if(argc < 2) {
        printf("Error: port number argument is required\n");
        return 0;
    }


    char buffer[1024] = { 0 };
    int PORT = strtol(argv[1], NULL, 10);
    string term_str = "\r\n\r\n";

    //setup socket
    int sockid = socket(AF_INET, SOCK_STREAM, 0);
    if (sockid == -1) {
        perror("Error during socket init");
        exit(1);
    }

    //fill in sockaddr
    struct sockaddr_in sock_addr;
    sock_addr.sin_family = htonl(AF_INET);
    sock_addr.sin_addr.s_addr = INADDR_ANY;
    sock_addr.sin_port = htons(PORT);

    //client sockaddr
    struct sockaddr_in cli_sock_addr;

    //bind socket to port
    int binding = bind(sockid, (struct sockaddr*) & sock_addr, sizeof(sock_addr));
    if (binding == -1) {
        perror("Error during binding");
        exit(1);
    }

    //listen
    int queueLimit = 0;
    int listener = listen(sockid, queueLimit);
    if (listener == -1) {
        perror("Error during listen");
        exit(1);
    }

    while(true) {
        //accept
        int cli_addrlen = sizeof(cli_sock_addr);
        int cli_sockid = accept(sockid, (struct sockaddr*) & cli_sock_addr, (socklen_t*)&cli_addrlen);
        if (cli_sockid == -1) {
            perror("Error during accept");
            exit(1);
        }

        //receive
        string received_str = sock_receive(cli_sockid, &cli_sock_addr, buffer, sizeof(buffer));

        printf("%s\n", received_str.c_str());
        reverse(received_str.begin(),received_str.end());

        //send
        sock_send(cli_sockid, received_str);

        //close
        close(cli_sockid);
    }

    return 0;
}

