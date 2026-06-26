# TLS Overview

TLS (Transport Layer Security) provides confidentiality, integrity, and
authentication on top of a transport protocol — almost always [[TCP — How it Works|TCP]].

## Handshake (TLS 1.3, simplified)

1. Client sends `ClientHello` with supported cipher suites and a key share
2. Server responds with `ServerHello`, its certificate, and its own key share
3. Both sides derive the same symmetric session key via Diffie-Hellman
4. Application data can now be encrypted with that session key

TLS 1.3 cut this down to one round trip (1-RTT) compared to TLS 1.2's 2-RTT,
which matters a lot for HTTPS latency — see [[HTTP and DNS]].

## Certificates

The server's certificate is signed by a Certificate Authority (CA) that the
client already trusts (root CAs are baked into the OS/browser). This is how
the client verifies it's actually talking to the real server and not a
man-in-the-middle.

> Self-signed certs skip the CA chain, which is why browsers warn you — there's
> no third party vouching for the identity.

Related: [[TCP — How it Works]], [[HTTP and DNS]]
