Alpha PNG Exporter - Starten
============================

1. ZIP entpacken.
2. ResolumeAlphaDropper.exe starten.
3. Ein einzelnes Input-Bild waehlen.
4. Output-Ordner pruefen oder auswaehlen.
5. Export-Typ waehlen:
   - Resolume: 1920x1080 transparente PNG fuer Arena/Avenue.
   - Shirt/Print: zugeschnittene transparente PNG fuer Shirtinator/Print-Seiten.
6. Convert druecken.
7. Die exportierte PNG-Datei verwenden.

Wichtig:
- Background Removal ist Pflicht. Wenn rembg/onnxruntime nicht funktioniert, bricht der Export mit Fehler ab.
- Resolume-Dateien enden auf _resolume.png.
- Shirt/Print-Dateien enden auf _shirt_print.png.
- Die App prueft, dass der Export PNG und transparent ist.
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
