class FilterModule(object):
    def filters(self):
        return {
            'format_ufw_ports': self.format_ufw_ports
        }

    def format_ufw_ports(self, port_dict: dict[str, list]) -> str:
        """
        Converts a dictionary of protocols and port lists into a UFW string.
        Input: {"tcp":[80, 443], "udp":[53, "120:129"]}
        Output: "80,443/tcp|53,120:129/udp"
        """
        if not isinstance(port_dict, dict):
            return ""

        parts = []

        # Loop through protocols in an organized order (tcp first, then udp, etc.)
        for proto in ['tcp', 'udp']:
            ports = port_dict.get(proto, [])
            
            # If the list exists and has items, format it
            if ports and isinstance(ports, list):
                ports_str = ",".join(str(p) for p in ports)
                parts.append(f"{ports_str}/{proto}")

        return "|".join(parts)
