from midealocal.discover import discover
from midea_beautiful import appliance_state

token = "2ca510843ccf4c233e4ce8c177c8c9b4a79d967417bdb8307e47239bb4dd8918555a738d618431a15336d62abb79dc2472e0684c9779ca34b8e75978733975ab"
key = "1d69090b797d41e8a7c029810933725f62f64be143764abaaa6badbbf602fe88"

discovered_devices = discover()
ip_addresses = [i['ip_address'] for i in discovered_devices.values()]

appliance = appliance_state(
    address=ip_addresses[0],
    token=token,
    key=key,
)

print(f"{appliance!r}")