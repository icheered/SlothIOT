# This file is executed on every boot (including wake-boot from deepsleep)
import esp
import gc
import machine
import network
import upip

from config import wifi_ssid, wifi_pass

def connect_wlan(ssid, password):
    """Connects build-in WLAN interface to the network.
    Args:
        ssid: Service name of Wi-Fi network.
        password: Password for that Wi-Fi network.
    Returns:
        True for success, Exception otherwise.
    """
    sta_if = network.WLAN(network.STA_IF)
    ap_if = network.WLAN(network.AP_IF)
    sta_if.active(True)
    ap_if.active(False)

    if not sta_if.isconnected():
        print("Connecting to WLAN ({})...".format(ssid))
        sta_if.active(True)
        sta_if.connect(ssid, password)
        while not sta_if.isconnected():
            pass

    return True


def main():
    """Main function. Runs after board boot, before main.py
    Connects to Wi-Fi and checks for latest OTA version.
    """
    esp.osdebug(None)

    gc.collect()
    gc.enable()

    # Wi-Fi credentials
    SSID = wifi_ssid
    PASSWORD = wifi_pass

    connect_wlan(SSID, PASSWORD)

    import senko
    from config import GITHUB_USER, GITHUB_REPO, GITHUB_DIR, GITHUB_BRANCH
    OTA = senko.Senko(user=GITHUB_USER, repo=GITHUB_REPO, working_dir=GITHUB_DIR, branch=GITHUB_BRANCH, files=["boot.py", "devices.py", "main.py"])

    if OTA.update():
        print("Updated to the latest version! Rebooting...")
        machine.reset()


if __name__ == "__main__":
    main()
