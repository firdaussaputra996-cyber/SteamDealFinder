"""
main.py

Entry point web app Steam Deal Finder.
Jalankan dengan: python main.py
Lalu buka: http://127.0.0.1:5000
"""

from __future__ import annotations

from typing import Optional

from flask import Flask, jsonify, render_template, request

from app.api.steam_api import SteamAPIError, SteamStoreClient
from app.core.search_service import game_to_dict, search_deals

FALLBACK_TAGS = [
    {"tagid": 19, "name": "Aksi"},
    {"tagid": 21, "name": "Petualangan"},
    {"tagid": 122, "name": "RPG"},
    {"tagid": 9, "name": "Strategi"},
    {"tagid": 599, "name": "Simulasi"},
    {"tagid": 701, "name": "Olahraga"},
    {"tagid": 699, "name": "Balapan"},
    {"tagid": 492, "name": "Indie"},
    {"tagid": 597, "name": "Kasual"},
]

app = Flask(__name__)
client = SteamStoreClient()


def _parse_optional_int(value: str | None, field_name: str) -> Optional[int]:
    if value is None or value == "":
        return None

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} harus berupa angka.") from exc

    if parsed < 0:
        raise ValueError(f"{field_name} tidak boleh negatif.")

    return parsed


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/genres")
def api_genres():
    try:
        tags = client.fetch_popular_tags(language="indonesian")
        return jsonify({"count": len(tags), "genres": tags})
    except SteamAPIError:
        return jsonify({"count": len(FALLBACK_TAGS), "genres": FALLBACK_TAGS})


@app.get("/api/search")
def api_search():
    try:
        query = request.args.get("query", "").strip()
        tag_id = _parse_optional_int(request.args.get("tag_id"), "Genre")
        min_price = _parse_optional_int(request.args.get("min_price"), "Harga minimum")
        max_price = _parse_optional_int(request.args.get("max_price"), "Harga maksimum")
        min_discount = _parse_optional_int(
            request.args.get("min_discount"), "Diskon minimum"
        )
        if min_discount == 0:
            min_discount = None

        if min_discount is not None and min_discount > 100:
            return jsonify({"error": "Diskon minimum tidak boleh lebih dari 100%."}), 400
        if min_price is not None and max_price is not None and min_price > max_price:
            return (
                jsonify(
                    {
                        "error": (
                            "Harga minimum tidak boleh lebih besar dari harga maksimum."
                        )
                    }
                ),
                400,
            )

        games = search_deals(
            client=client,
            query=query,
            tag_id=tag_id,
            min_price=min_price,
            max_price=max_price,
            min_discount=min_discount,
        )

        return jsonify(
            {
                "count": len(games),
                "results": [game_to_dict(game) for game in games],
            }
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except SteamAPIError as exc:
        return jsonify({"error": str(exc)}), 502
    except Exception as exc:
        return jsonify({"error": f"Terjadi kesalahan tak terduga: {exc}"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
