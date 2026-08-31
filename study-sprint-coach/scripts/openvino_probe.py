"""Report locally discoverable OpenVINO acceleration devices."""

import importlib
import json
import sys


# OpenVINO documents Core().available_devices as the device capability API.
DEVICE_SOURCE_URL = "https://docs.openvino.ai/nightly/openvino-workflow/running-inference/inference-devices-and-modes/query-device-properties.html"
# OpenVINO documents this import and Core() call as installation verification.
INSTALL_SOURCE_URL = "https://docs.openvino.ai/nightly/get-started/install-openvino/install-openvino-pip.html"
NEXT_ACTION = "Install or repair the local OpenVINO runtime, then rerun this probe. Do not claim CPU/GPU/NPU acceleration until devices are listed."


def probe_openvino(import_module=importlib.import_module) -> dict:
    try:
        module = import_module("openvino")
        core = module.Core()
        return {
            "available": True,
            "version": getattr(module, "__version__", "unknown"),
            "devices": sorted(str(device) for device in core.available_devices),
            "source": DEVICE_SOURCE_URL,
        }
    except Exception as error:
        return {
            "available": False,
            "error": f"{type(error).__name__}: {error}",
            "next_action": NEXT_ACTION,
            "source": INSTALL_SOURCE_URL,
        }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(probe_openvino(), ensure_ascii=False))
