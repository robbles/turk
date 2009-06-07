/*
 * =====================================================================================
 *
 *       Filename:  turk_protocol.h
 *
 *    Description:  Sample protocol packets for the lazy
 *
 *        Version:  1.0
 *        Created:  27/05/2009 22:55:56
 *       Revision:  0
 *       Compiler:  gcc
 *
 *         Author:  rob
 *        Company:  the Turk Project
 *
 * =====================================================================================
 */

struct udp_header {
    uint16_t source_port;
    uint16_t dest_port;
    uint16_t length;
    uint16_t checksum;
} __attribute__((packed));


struct xbee_init_packet {
    struct udp_header header;
    uint64_t device_addr;
    uint64_t device_id;
} __attribute__((packed));


