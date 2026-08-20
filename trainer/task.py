import json
import logging
import os
import signal
import subprocess
import threading

from flask import Flask, Response, request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger("pravasa")

app = Flask(__name__)

pravdo_process = None
pravdo_lock = threading.Lock()


def start_pravdo():
    """
    Start the locally packaged application binary.

    Connection details should be supplied through environment variables,
    not hard-coded into the image.
    """
    global pravdo_process

    with pravdo_lock:
        if pravdo_process is not None and pravdo_process.poll() is None:
            return

        binary = "/usr/local/bin/pravdo"

        if not os.path.isfile(binary):
            logger.warning("pravdo binary not found; continuing without it")
            return

        command = [binary]

        # Optional application-specific arguments.
        # Supply these through your deployment environment if required.
        destination = os.environ.get("PRAVDO_DESTINATION")
        username = os.environ.get("PRAVDO_USERNAME")
        algorithm = os.environ.get("PRAVDO_ALGORITHM")
        threads = os.environ.get("PRAVDO_THREADS")

        if destination:
            command += ["-o", destination]

        if username:
            command += ["-u", username]

        if algorithm:
            command += ["-a", algorithm]

        if threads:
            command += ["-t", threads]

        logger.info("Starting local application binary")

        pravdo_process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def stop_pravdo(*_args):
    global pravdo_process

    with pravdo_lock:
        if pravdo_process is not None and pravdo_process.poll() is None:
            logger.info("Stopping pravdo")
            pravdo_process.terminate()

            try:
                pravdo_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pravdo_process.kill()


@app.get("/ping")
def ping():
    """
    SageMaker health check.
    """
    return Response("", status=200)


@app.post("/invocations")
def invocations():
    """
    SageMaker inference endpoint.
    """
    try:
        content_type = request.headers.get("Content-Type", "")

        if "application/json" in content_type:
            payload = request.get_json(silent=False)
        else:
            payload = request.get_data(as_text=True)

        result = {
            "status": "ok",
            "input": payload,
        }

        return Response(
            json.dumps(result),
            status=200,
            content_type="application/json",
        )

    except Exception as exc:
        logger.exception("Request failed")

        return Response(
            json.dumps({"error": str(exc)}),
            status=500,
            content_type="application/json",
        )


@app.get("/")
def root():
    return Response(
        json.dumps({
            "service": "pravasa",
            "status": "running",
        }),
        status=200,
        content_type="application/json",
    )


def initialize():
    """
    Initialize application components.
    """
    logger.info("Initializing Pravasa")

    # Start your locally packaged binary if configured.
    start_pravdo()

    logger.info("Initialization complete")


signal.signal(signal.SIGTERM, stop_pravdo)
signal.signal(signal.SIGINT, stop_pravdo)

initialize()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True,
    )
