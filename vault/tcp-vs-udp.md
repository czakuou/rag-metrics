# TCP vs UDP

Quick comparison note — exam loves asking "which one would you use for X".

## TCP

- Connection-oriented (handshake required — see [[TCP — How it Works]])
- Reliable: guarantees delivery, retransmits lost packets
- Ordered: guarantees byte stream arrives in order
- Has flow control and congestion control
- Higher overhead per packet (headers, ACKs, handshake latency)
- Use for: web browsing (HTTP/HTTPS), email, file transfer — anything where
  correctness matters more than raw speed

## UDP

- Connectionless: no handshake, just fire packets ("datagrams")
- Unreliable: no delivery guarantee, no retransmission
- Unordered: packets can arrive in any order, or not at all
- No flow/congestion control built in (the application must implement its
  own if needed)
- Lower overhead, lower latency
- Use for: video/voice calls (a late packet is useless anyway, better to
  drop it and move on), DNS lookups (single small request/response, retry
  at the application level is cheap), online games (favor latency over
  reliability for position updates)

## When should I use TCP?

Use TCP whenever losing or reordering data would break correctness and
you're willing to pay extra latency for that guarantee: file downloads,
database connections, any RPC where the client needs to know the call
actually succeeded. If a single dropped byte corrupts the whole transfer
(like downloading a zip file), you want TCP's retransmission guarantees, not
UDP's "best effort and move on."

> DNS technically can use either — primarily UDP for normal queries, falling
> back to TCP for large responses (like zone transfers). Mentioned in
> [[HTTP and DNS]] too.

Related: [[TCP — How it Works]], [[HTTP and DNS]]
