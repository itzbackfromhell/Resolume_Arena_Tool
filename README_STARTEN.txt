Resolume Alpha Dropper - Starten
================================

1. ZIP entpacken.
2. ResolumeAlphaDropper.exe starten.
3. Input-Bild oder Batch-Ordner waehlen.
4. Preset waehlen.
5. Output-Ordner pruefen.
6. Export druecken.

Wichtig:
- Die App veraendert Resolume nicht.
- Exporte landen im Ordner output, wenn kein anderer Output-Ordner gewaehlt wird.
- Logs und Diagnoseberichte landen im Ordner logs.
- Wenn Background Removal benutzt wird, kann der erste Start laenger dauern, weil ein AI-Modell geladen wird.

Fehlerdiagnose:
- In der Entwickler-Version:
  python -m resolume_alpha_tool.cli diagnostics
- Im Portable-Build spaeter ueber das Diagnostics-Menue oder Support-Report.

Ordnerstruktur:

ResolumeAlphaDropper/
  ResolumeAlphaDropper.exe
  presets/
  output/
  logs/
  README_STARTEN.txt
