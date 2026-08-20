import json
import logging
import os

from flask import Flask, Response, request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger("testo")

app = Flask(__name__)


@app.get("/ping")
def ping():
    logger.info("SageMaker ping received")
    return Response("", status=200)


@app.post("/invocations")
def invocations():
    try:
        content_type = request.headers.get("Content-Type", "")

        if "application/json" in content_type:
            payload = request.get_json(silent=False)
        else:
            payload = request.get_data(as_text=True)

        logger.info("Invocation received")

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
        logger.exception("Invocation failed")

        return Response(
            json.dumps({
                "error": str(exc),
            }),
            status=500,
            content_type="application/json",
        )


@app.get("/")
def root():
    return Response(
        json.dumps({
            "service": "testo",
            "status": "running",
        }),
        status=200,
        content_type="application/json",
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True,
    )
