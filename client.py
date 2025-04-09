#!/usr/bin/env python3
import socket
import struct
import sys

# Indirizzo e porta del server DNS da testare
SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 2053
TIMEOUT_SECONDS = 5

def build_dummy_query():
    """
    Costruisce una query DNS dummy.
    Non importa il contenuto della query perché il server dovrebbe rispondere
    sempre con header e question section fissi.
    
    L'header dummy viene costruito con:
    - Transaction ID: 0xabcd (valore arbitrario per la query)
    - Flags: 0x0100 (query standard, recursion desired)
    - QDCOUNT = 1, ANCOUNT = 0, NSCOUNT = 0, ARCOUNT = 0
    
    La sezione question viene impostata per "example.com" e non viene utilizzata dal server.
    """
    transaction_id = 0xabcd
    flags = 0x0100    # Query standard con recursion desired
    qdcount = 1
    ancount = 0
    nscount = 0
    arcount = 0
    header = struct.pack("!6H", transaction_id, flags, qdcount, ancount, nscount, arcount)
    
    # Costruzione della sezione question per "example.com":
    # Formato: <lunghezza><etichetta> ... terminata da 0x00, seguita da 2 byte per tipo e 2 byte per classe
    domain = b'\x07example\x03com\x00'
    qtype = struct.pack("!H", 1)   # Tipo A
    qclass = struct.pack("!H", 1)  # Classe IN
    question = domain + qtype + qclass
    
    return header + question

def parse_dns_response(response):
    """
    Dato il pacchetto di risposta DNS, effettua il parsing dell'header e restituisce:
    - id_field: ID del messaggio (2 byte)
    - flags: campo flags (2 byte)
    - qdcount: numero di domande (2 byte)
    - ancount: numero di risposte (2 byte)
    - nscount: numero di authority (2 byte)
    - arcount: numero di additional (2 byte)
    - question_section: il resto della risposta (la sezione question)
    """
    if len(response) < 12:
        raise ValueError("Risposta troppo breve per contenere un header DNS valido.")
    
    header = response[:12]
    id_field, flags, qdcount, ancount, nscount, arcount = struct.unpack("!6H", header)
    question_section = response[12:]
    return id_field, flags, qdcount, ancount, nscount, arcount, question_section

def main():
    # Creazione della query dummy da inviare
    query_packet = build_dummy_query()
    print("Query DNS inviata (header + question dummy):", query_packet.hex())

    # Creazione di un socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT_SECONDS)
    
    try:
        # Invia la query al server DNS
        sock.sendto(query_packet, (SERVER_ADDRESS, SERVER_PORT))
        print(f"Inviata query a {SERVER_ADDRESS}:{SERVER_PORT}")

        # Attendi la risposta (fino a 512 byte)
        response, addr = sock.recvfrom(512)
        print(f"Risposta ricevuta da {addr}: {response.hex()}")
    except socket.timeout:
        print(f"Errore: Timeout dopo {TIMEOUT_SECONDS} secondi senza risposta dal server.")
        sys.exit(1)
    finally:
        sock.close()

    # Parsing dell'header e della sezione question
    try:
        id_field, flags, qdcount, ancount, nscount, arcount, question_section = parse_dns_response(response)
    except Exception as e:
        print("Errore nel parsing della risposta:", e)
        sys.exit(1)
    
    # Verifica dell'header
    expected_id = 1234
    if id_field != expected_id:
        print(f"Test fallito: ID atteso {expected_id}, ottenuto {id_field}.")
        sys.exit(1)
    else:
        print("Campo ID verificato: 1234")
    
    expected_flags = 0x8000  # Solo il bit di risposta impostato (1 << 15)
    if flags != expected_flags:
        print(f"Test fallito: Flags attesi {expected_flags:#06x}, ottenuti {flags:#06x}.")
        sys.exit(1)
    else:
        print("Campo Flags verificato: 0x8000")
    
    if qdcount != 1:
        print(f"Test fallito: QDCOUNT atteso 1, ottenuto {qdcount}.")
        sys.exit(1)
    else:
        print("Campo QDCOUNT verificato: 1")
    
    if ancount != 0 or nscount != 0 or arcount != 0:
        print("Test fallito: ANCOUNT, NSCOUNT e ARCOUNT devono essere tutti 0.")
        print(f"Ottenuti - ANCOUNT: {ancount}, NSCOUNT: {nscount}, ARCOUNT: {arcount}")
        sys.exit(1)
    else:
        print("ANCOUNT, NSCOUNT e ARCOUNT verificati: tutti a 0")
    
    # Verifica della sezione question
    expected_question = b'\x0ccodecrafters\x02io\x00' + struct.pack("!H", 1) + struct.pack("!H", 1)
    expected_len = len(expected_question)
    if len(question_section) < expected_len:
        print("Test fallito: la sezione question nella risposta è troppo corta.")
        sys.exit(1)
    
    # Prendiamo esattamente il numero di byte attesi dalla sezione question
    question_bytes = question_section[:expected_len]
    if question_bytes != expected_question:
        print("Test fallito: la sezione question non corrisponde ai byte attesi.")
        print("Atteso:", expected_question.hex())
        print("Ottenuto:", question_bytes.hex())
        sys.exit(1)
    else:
        print("Sezione question verificata con successo.")
    
    print("Tutti i test sono stati superati con successo.")

if __name__ == "__main__":
    main()
