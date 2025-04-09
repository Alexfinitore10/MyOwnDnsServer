#include <iostream>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <vector>

struct DNS_message
{
    uint16_t ID;
    uint16_t flags;
    uint16_t qd; //question, usually just 1
    uint16_t an;
    uint16_t ns;
    uint16_t ar;
};

struct DNS_question
{
    std::vector<std::string> name;
    u_short type;
    u_short qclass;

    //funzione per l'encoding
    std::vector<uint8_t> serialize(){
        std::vector<uint8_t> data = encode_domain(name);
        uint16_t t = htons(type);
        uint16_t c = htons(qclass);
        data.insert(data.end(), reinterpret_cast<uint8_t*>(&t), reinterpret_cast<uint8_t*>(&t) + 2);
        data.insert(data.end(), reinterpret_cast<uint8_t*>(&c), reinterpret_cast<uint8_t*>(&c) + 2);
        return data;

    }
};



DNS_message makeHeader(DNS_message);
DNS_message makeResponse(DNS_message);
std::vector<uint8_t> encode_domain(std::vector<std::string>&);


int main() {
    // Flush after every std::cout / std::cerr
    std::cout << std::unitbuf;
    std::cerr << std::unitbuf;

    // Disable output buffering
    setbuf(stdout, NULL);

    // You can use print statements as follows for debugging, they'll be visible when running tests.
    std::cout << "1 from your program will appear here!" << std::endl;

      // Uncomment this block to pass the first stage
   int udpSocket;
   struct sockaddr_in clientAddress;//classica struttura dati delle socket, come in C

   udpSocket = socket(AF_INET, SOCK_DGRAM, 0);//Sock_Dgram è per UDP
   if (udpSocket == -1) {
       std::cerr << "Socket creation failed: " << strerror(errno) << "..." << std::endl;
       return 1;
   }

   // Since the tester restarts your program quite often, setting REUSE_PORT
   // ensures that we don't run into 'Address already in use' errors
   int reuse = 1;
   if (setsockopt(udpSocket, SOL_SOCKET, SO_REUSEPORT, &reuse, sizeof(reuse)) < 0) {
       std::cerr << "SO_REUSEPORT failed: " << strerror(errno) << std::endl;
       return 1;
   }

   sockaddr_in serv_addr = { .sin_family = AF_INET,
                             .sin_port = htons(2053),
                             .sin_addr = { htonl(INADDR_ANY) },
                           };

   if (bind(udpSocket, reinterpret_cast<struct sockaddr*>(&serv_addr), sizeof(serv_addr)) != 0) {
       std::cerr << "Bind failed: " << strerror(errno) << std::endl;
       return 1;
   }

   int bytesRead;
   char buffer[512];
   socklen_t clientAddrLen = sizeof(clientAddress);

   while (true) {
       // Receive data
       bytesRead = recvfrom(udpSocket, buffer, sizeof(buffer), 0, reinterpret_cast<struct sockaddr*>(&clientAddress), &clientAddrLen);
       if (bytesRead == -1) {
           perror("Error receiving data");
           break;
       }

       buffer[bytesRead] = '\0';
       std::cout << "Received " << bytesRead << " bytes: " << buffer << std::endl;
/* 
       if(bytesRead != 12)
       {
        std::cout<<"Richiesta DNS non consona, non sono arrivati 12 bytes"<<std::endl;
        continue;
       } */

       DNS_message message;

       message = makeHeader(message);
       message = makeResponse(message);

       // Send response
       if (sendto(udpSocket, &message, sizeof(message), 0, reinterpret_cast<struct sockaddr*>(&clientAddress), sizeof(clientAddress)) == -1) {
           perror("Failed to send response");
       }
   }

   close(udpSocket);

    return 0;
}

DNS_message makeHeader(DNS_message message)
{
    message.ID = htons(1234);
    uint16_t flags = (1 << 15) |
    (0 << 11) |  // Opcode = 0 (Standard Query)
    (0 << 10) |  // AA = 0 (Non autoritativo)
    (0 << 9)  |  // TC = 0 (Non troncato)
    (0 << 8)  |  // RD = 0 (Nessuna ricorsione richiesta)
    (0 << 7)  |  // RA = 0 (Nessuna ricorsione disponibile)
    (0 << 6)  |  // Z = 0
    (0 << 5)  |  // Z = 0
    (0 << 4)  |  // Z = 0
    (0 << 0);
    message.flags = htons(flags);
    message.qd = 0;
    message.an = 0;
    message.ns = 0;
    message.ar = 0;
    std::cout<<flags<<std::endl;
    std::cout<<message.flags<<std::endl;

    std::cout<<std::endl;
    std::cout<<std::hex<< message.flags << "\n";
    return message;
}

DNS_message makeResponse(DNS_message message)
{
    message.qd = htons(message.qd++);

}

std::vector<uint8_t> encode_domain(std::vector<std::string>& dominio)
{
    std::vector<uint8_t> encoded;
    for (auto& label : dominio)
    {
        encoded.push_back(static_cast<uint8_t>(label.size()));//questo è per l'etichetta \x06 es.
        encoded.insert(encoded.end(), label.begin(), label.end());//inserisce i caratteri
    }
    encoded.push_back(0);//inserisce il byte finale, già formattato, credo
    return encoded;
}



