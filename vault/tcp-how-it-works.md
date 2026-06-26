# TCP — How it Works

## The three-way handshake

Before any data is sent, TCP establishes a connection:
1. Client sends `SYN` (synchronize) with an initial sequence number
2. Server responds `SYN-ACK` (acknowledging the client's sequence number,
   plus its own initial sequence number)
3. Client sends `ACK`, connection is established

This handshake is why TCP is "connection-oriented" — both sides agree on
initial state before exchanging application data. Compare to [[TCP vs UDP]]
where UDP skips this entirely.

## Reliability

TCP guarantees delivery and ordering using sequence numbers and
acknowledgements. Every byte sent has a sequence number; the receiver sends
ACKs back. If the sender doesn't get an ACK within a timeout, it
retransmits. Out-of-order packets are buffered and reassembled in the
correct order before being handed to the application.

## Flow control

The receiver advertises a "window size" — how many bytes it's willing to
buffer before the application reads them. The sender can't send more than
this window allows, preventing the sender from overwhelming a slow receiver.
This is the sliding window protocol.

## Congestion control

Separate from flow control, congestion control protects the *network* (not
just the receiver) from being overwhelmed. TCP starts with a small
congestion window and grows it (slow start), backing off sharply when packet
loss is detected (interpreted as a sign of congestion). Algorithms like
Reno, Cubic, and BBR differ in exactly how aggressively they grow/shrink
this window.

## Connection teardown

Closing a TCP connection uses a four-way handshake (`FIN`, `ACK`, `FIN`,
`ACK`) since either side can close its half of the connection independently
— TCP is technically full-duplex, so one side can stop sending while still
receiving.

Related: [[TCP vs UDP]], [[HTTP and DNS]], [[TLS Overview]]
