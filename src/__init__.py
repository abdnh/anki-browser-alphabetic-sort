from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Sequence, cast

from anki.cards import Card
from anki.hooks import addHook
from anki.notes import Note, NoteId
from aqt import appVersion, gui_hooks, mw

ADDON_DIR = Path(__file__).parent
sys.path.append(str(ADDON_DIR / "vendor"))

# pylint: disable=wrong-import-position
import pyuca
import pyuca.collator

ANKI_VERSION = tuple(int(p) for p in appVersion.split("."))

if TYPE_CHECKING or ANKI_VERSION >= (2, 1, 45):
    # pylint: disable=ungrouped-imports
    from anki.collection import BrowserColumns
    from aqt.browser import CellRow, Column, ItemId, SearchContext
    from aqt.browser.table import ItemId


class Collation(Enum):
    UNICASE = 1
    UNICODE = 2


COLUMN_KEY = "alphabeticSortField"
COLUMN_LABEL = "Sort Field (Alphabetic)"
COLLATION = Collation.UNICODE


def add_browser_column(columns: dict[str, Column]) -> None:
    columns[COLUMN_KEY] = Column(
        key=COLUMN_KEY,
        cards_mode_label=COLUMN_LABEL,
        notes_mode_label=COLUMN_LABEL,
        sorting=BrowserColumns.SORTING_ASCENDING,
        uses_cell_font=True,
        alignment=BrowserColumns.ALIGNMENT_START,
        cards_mode_tooltip="",
        notes_mode_tooltip="",
    )


def on_search(context: SearchContext) -> None:
    if isinstance(context.order, Column) and context.order.key == COLUMN_KEY:
        if COLLATION == Collation.UNICASE:
            context.order = "n.sfld collate unicase %s" % (
                "desc" if context.reverse else "asc"
            )
        else:
            sort_col = mw.col.get_browser_column("noteFld")
            sort_col.notes_mode_label = COLUMN_LABEL
            context.order = sort_col


def on_browser_did_fetch_row(
    card_or_note_id: ItemId, is_note: bool, row: CellRow, columns: Sequence[str]
) -> None:
    try:
        idx = columns.index(COLUMN_KEY)
    except ValueError:
        return
    try:
        sort_field_col_idx = columns.index("noteFld")
    except ValueError:
        sort_field_col_idx = -1
    if sort_field_col_idx >= 0:
        row.cells[idx].text = row.cells[sort_field_col_idx].text
        row.cells[idx].is_rtl = row.cells[sort_field_col_idx].is_rtl
    else:
        if is_note:
            nid = cast(NoteId, card_or_note_id)
        else:
            nid = mw.col.db.scalar(
                "select nid from cards where id = ?", card_or_note_id
            )
        sfld = mw.col.db.scalar("select sfld from notes where id = ?", nid)
        row.cells[idx].text = sfld
        mid = mw.col.get_note(nid).mid
        notetype = mw.col.models.get(mid)
        sortf = notetype["sortf"]
        row.cells[idx].is_rtl = notetype["flds"][sortf]["rtl"]


def unicode_sort(collator: pyuca.Collator, item_id: ItemId) -> tuple:
    sfld = mw.col.db.scalar("select sfld from notes where id = ?", item_id)
    if not sfld:
        sfld = mw.col.db.scalar(
            "select sfld from notes where id in (select nid from cards where id = ? limit 1)",
            item_id,
        )
    if not sfld:
        sfld = ""
    sfld = str(sfld)
    return collator.sort_key(sfld)


def on_browser_did_search(context: SearchContext) -> None:
    if not context.ids:
        return
    if COLLATION == Collation.UNICODE and (
        (
            isinstance(context.order, Column)
            and context.order.notes_mode_label == COLUMN_LABEL
        )
        # Advanced Browser
        or (
            isinstance(context.order, str) and "n.sfld collate unicase" in context.order
        )
    ):
        collator = pyuca.Collator()
        context.ids = sorted(context.ids, key=lambda i: unicode_sort(collator, i))


advanced_browser_column: Any = None


def on_advanced_browser_loaded(advanced_browser: Any) -> None:
    def on_data(card: Card, note: Note, _type: str) -> str:
        return mw.col.db.scalar("select sfld from notes where id = ?", note.id)

    def on_sort() -> str:
        return "n.sfld collate unicase asc"

    global advanced_browser_column
    advanced_browser_column = advanced_browser.newCustomColumn(
        COLUMN_KEY, COLUMN_LABEL, on_data, onSort=on_sort
    )


def on_advanced_browser_build_context_menu(context_menu: Any) -> None:
    context_menu.addItem(advanced_browser_column)


def setup_hooks() -> None:
    if ANKI_VERSION >= (2, 1, 45):
        gui_hooks.browser_did_fetch_columns.append(add_browser_column)
        gui_hooks.browser_will_search.append(on_search)
        gui_hooks.browser_did_fetch_row.append(on_browser_did_fetch_row)
    else:
        addHook("advBrowserLoaded", on_advanced_browser_loaded)
        addHook("advBrowserBuildContext", on_advanced_browser_build_context_menu)
    gui_hooks.browser_did_search.append(on_browser_did_search)


setup_hooks()
