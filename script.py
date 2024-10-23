from mitmproxy import http
import logging

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a file handler
handler = logging.FileHandler('test.log')
handler.setLevel(logging.INFO)

# Create a formatter and set it for the handler
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

def request(flow: http.HTTPFlow) -> None:
    # Log request URL
    print(f"Request: {flow.request.url}")
    logger.info(f"Request: {flow.request.url}")

def response(flow: http.HTTPFlow) -> None:
    # Log response URL
    print(f"Response: {flow.response.url}")
    logger.info(f"Response: {flow.response.url}")

def http_connect(flow: http.HTTPFlow) -> None:
    # Log HTTPS requests
    print(f"HTTPS Request: {flow.request.url}")
    logger.info(f"HTTPS Request: {flow.request.url}")