# HTTP and DNS

Networking lecture, week 6. Quick notes on how a browser actually gets a page.

## DNS resolution

Before any HTTP request, the domain name needs to be resolved to an IP
address. The lookup chain is: browser cache -> OS cache -> recursive resolver
(usually your ISP or 1.1.1.1/8.8.8.8) -> root nameserver -> TLD nameserver
(e.g. `.com`) -> authoritative nameserver for the domain. Results are cached
at every level according to the record's TTL.

## HTTP basics

HTTP is a request-response protocol. A request has a method (GET, POST, PUT,
DELETE, etc.), headers, and optionally a body. A response has a status code
(2xx success, 3xx redirect, 4xx client error, 5xx server error), headers, and
a body.

HTTP/1.1 introduced persistent connections (keep-alive) so you don't need a
new TCP handshake per request — see [[TCP — How it Works]] for what that
handshake actually involves. HTTP/2 added multiplexing (multiple requests
over one connection, no head-of-line blocking at the HTTP layer) and header
compression.

## Where TLS fits

HTTPS is HTTP over TLS — see [[TLS Overview]]. The TLS handshake happens
before any HTTP data is exchanged, adding round trips (mitigated by TLS 1.3's
1-RTT handshake, down from 2-RTT in TLS 1.2).

Related: [[TCP — How it Works]], [[TCP vs UDP]]
