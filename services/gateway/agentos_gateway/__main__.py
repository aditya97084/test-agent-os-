import uvicorn

from agentos_contracts.config import get_settings


def main() -> None:
    s = get_settings()
    uvicorn.run("agentos_gateway.main:app", host=s.gateway_host, port=s.gateway_port, log_level="info")


if __name__ == "__main__":
    main()
