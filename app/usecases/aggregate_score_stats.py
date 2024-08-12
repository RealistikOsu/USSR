import app.state.services


async def total_scores_set() -> int:
    return sum(
        [
            await app.state.services.database.fetch_val(
                f"""\
                SELECT count(*)
                FROM {table}
                """,
            )
            for table in ("scores", "scores_relax", "scores_ap")
        ]
    )
