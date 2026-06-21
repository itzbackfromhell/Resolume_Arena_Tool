Resolume Alpha Dropper - Starten
================================

1. ZIP entpacken.
2. ResolumeAlphaDropper.exe starten.
3. Ein einzelnes Input-Bild waehlen.
4. Output-Ordner pruefen oder auswaehlen.
5. Convert image for Resolume druecken.
6. Die exportierte PNG-Datei in Resolume ziehen/importieren.

Wichtig:
- Die GUI ist absichtlich simpel: ein Bild rein, Background weg, Resolume-PNG raus.
- Background Removal ist Pflicht. Wenn rembg/onnxruntime nicht funktioniert, bricht der Export mit Fehler ab.
- Die App prueft, dass der Export PNG, 1920x1080 und transparent ist.
- Die App veraendert Resolume nicht.
- Exporte landen im Ordner output, wenn kein anderer Output-Ordner gewaehlt wird.
- Es wird nicht ueberschrieben; existierende Zieldateien bekommen automatisch nummerierte Namen.
- Der erste Background-Removal-Export kann laenger dauern, weil ein lokales AI-Modell geladen wird.
- Fuer Background Removal auf Windows eine normale CPython-x64-Version nutzen.
- Nicht Python314t/free-threaded fuer rembg/onnxruntime verwenden.

Fehlerdiagnose in der Entwickler-Version:
  python -m resolume_alpha_tool.cli rembg-check

Ordnerstruktur:

ResolumeAlphaDropper/
  ResolumeAlphaDropper.exe
  output/
  README_STARTEN.txt
