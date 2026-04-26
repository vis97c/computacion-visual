from __future__ import annotations

import argparse
import asyncio
import json
import random

import websockets

COLORS = ("red", "green", "blue")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Servidor WebSocket que envia datos visuales en tiempo real."
    )
    parser.add_argument("--host", default="localhost", help="Host de escucha.")
    parser.add_argument("--port", type=int, default=8765, help="Puerto de escucha.")
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Intervalo de envio en segundos.",
    )
    parser.add_argument(
        "--range-min",
        type=float,
        default=-5.0,
        help="Valor minimo para x/y.",
    )
    parser.add_argument(
        "--range-max",
        type=float,
        default=5.0,
        help="Valor maximo para x/y.",
    )
    return parser.parse_args()


def build_payload(range_min: float, range_max: float) -> dict[str, float | str]:
    return {
        "x": random.uniform(range_min, range_max),
        "y": random.uniform(range_min, range_max),
        "color": random.choice(COLORS),
    }


def make_handler(
    interval_s: float, range_min: float, range_max: float
):
    async def handler(websocket) -> None:
        remote = websocket.remote_address
        print(f"Cliente conectado: {remote}")
        try:
            while True:
                payload = build_payload(range_min=range_min, range_max=range_max)
                await websocket.send(json.dumps(payload))
                await asyncio.sleep(interval_s)
        finally:
            print(f"Cliente desconectado: {remote}")

    return handler


async def run_server(args: argparse.Namespace) -> None:
    if args.interval <= 0:
        raise ValueError("--interval debe ser mayor a 0.")
    if args.range_min >= args.range_max:
        raise ValueError("--range-min debe ser menor que --range-max.")
    if args.port <= 0:
        raise ValueError("--port debe ser mayor a 0.")

    handler = make_handler(
        interval_s=args.interval,
        range_min=args.range_min,
        range_max=args.range_max,
    )
    async with websockets.serve(handler, args.host, args.port):
        print(f"Servidor WebSocket activo en ws://{args.host}:{args.port}")
        await asyncio.Future()


def main() -> None:
    args = parse_args()
    asyncio.run(run_server(args))


if __name__ == "__main__":
    main()
