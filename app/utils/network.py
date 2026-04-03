import ipaddress
import logging

logger = logging.getLogger(__name__)


def validate_same_network(client_ip: str, teacher_ip: str, prefix_len: int = 16) -> bool:
    """Check if client and teacher are on the same subnet using standard ipaddress library."""
    try:
        client = ipaddress.ip_address(client_ip)
        teacher = ipaddress.ip_address(teacher_ip)

        # Basic security: both must be private
        if not client.is_private or not teacher.is_private:
            logger.warning(f"Public IP detected in local check (Client={client_ip}, Teacher={teacher_ip}). Refusing.")
            return False

        client_net = ipaddress.ip_network(f"{client_ip}/{prefix_len}", strict=False)
        teacher_net = ipaddress.ip_network(f"{teacher_ip}/{prefix_len}", strict=False)

        result = client_net == teacher_net
        if not result:
            logger.info(f"Subnet mismatch. Client in '{client_net}', Teacher in '{teacher_net}'.")
        return result
    except ValueError as e:
        logger.error(f"Invalid IP passed for network validation: {e}")
        return False
