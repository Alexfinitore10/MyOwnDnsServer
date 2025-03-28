import socket
import struct

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2)  # Set a 2-second timeout

server_address = ('localhost', 2053)

# Construct a minimal DNS query header (12 bytes)
query_id = 0x1234  # Arbitrary ID for the query
flags = 0x0000     # Standard query with recursion desired
qdcount = 1         # One question
ancount = 0
nscount = 0
arcount = 0

# Pack the DNS header fields into bytes (network byte order)
query_header = struct.pack('!HHHHHH', query_id, flags, qdcount, ancount, nscount, arcount)

try:
    # Send the query to the DNS server
    sent = sock.sendto(query_header, server_address)
    print(f"Sent {sent} byte query")

    # Receive the response
    data, addr = sock.recvfrom(1024)
    print(f"Received {len(data)} byte response from {addr}")

    # Parse the DNS header from the response
    if len(data) < 12:
        raise ValueError("Response too short to contain DNS header")

    response_id, response_flags, qd, an, ns, ar = struct.unpack('!HHHHHH', data[:12])

    print("\nParsed response header:")
    print(f"Transaction ID: {response_id}")
    print(f"Flags: 0x{response_flags:04x}")
    print(f"Questions: {qd}, Answers: {an}, Authority: {ns}, Additional: {ar}")

    # Validate the response
    assert response_id == 1234, f"Expected ID 1234, got {response_id}"
    assert (response_flags & 0x8000) == 0x8000, "QR bit not set (not a response)"
    assert qd == 0, "Question count should be 0 in response"
    assert an == 0, "Answer count should be 0"
    assert ns == 0, "Authority count should be 0"
    assert ar == 0, "Additional count should be 0"

    print("\nAll tests passed!")

except socket.timeout:
    print("\nERROR: No response received (timeout)")
    exit(1)
except Exception as e:
    print(f"\nERROR: {e}")
    exit(1)
finally:
    sock.close()

