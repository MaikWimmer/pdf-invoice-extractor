"""Sample page content shared by the tests.

Kept out of ``conftest.py`` so the raw building blocks can be imported
directly by tests that need to mutate them.
"""

HEADER = """MUSTERFIRMA Technik GmbH
Beispielweg 1, 12345 Musterstadt
Rechnung Nr. 2026-0341
Rechnungsdatum: 02.06.2026
Kunde: Muster Handels GmbH
"""

TABLE = [
    ["Position", "Menge", "Einzelpreis", "Summe"],
    ["Wartungsvertrag Juni", "1", "249,00", "249,00"],
    ["Ersatzteil-Set A", "2", "89,50", "179,00"],
    ["Anfahrtspauschale", "1", "45,00", "45,00"],
    ["Gesamtbetrag netto", "", "", "473,00"],
    ["zzgl. 19% MwSt.", "", "", "89,87"],
    ["Rechnungsbetrag", "", "", "562,87"],
]
