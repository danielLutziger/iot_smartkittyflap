# ZHAW Gruppenarbeit im Modul IoT - Smart Kitty Flap
Das Ziel des Projektes ist es, festzustellen, ob eine Katze mit einer Beute (z.B. Maus) ins Haus reinkommen will. In so einer Situation sollte letztlich das Katzentor verschlossen werden, bis die Katze wieder ohne Beute gesichtet wird. Dafür wurde ein Raspberry Pi mit einer Kamera, die über einem Katzentor installiert wird, verwendet.
Die Bildanalyse mittels TensorFlow Lite erkennt Objekte, die sich vor der Kamera (in diesem Fall eine USB-Webcam) befindet und erkennt Katzen, Mäuse und somit auch beide zusammen. In einem solchen Fall wird einerseits eine WhatsApp-Nachricht via Twilio versendet, ein Log geschrieben und ein Snapshot der Kamera gespeichert. Die Daten werden ausserdem über MQTT "published" und letztendlich in einem Node-RED-Dashboard angezeigt.
Das Node-RED-Dashboard implementiert ausserdem weitere Elemente wie die Wetterabfrage über openweathermap, eine Visualisierung des Katzentor-Status simuliert als SVG-Grafik, wesentliche KPIs der Auslastung des Pi's (Temperatur, CPU, ...) oder auch die Anzeige der letzten Logs inkl. Snapshots.


![Top Tier Engineering](https://github.com/lutzidan/iot_smartkittyflap/blob/main/Images/sc1.jpeg)
![Top Tier Engineering](https://github.com/lutzidan/iot_smartkittyflap/blob/main/Images/sc2.jpeg)

![Top Tier Engineering](https://github.com/lutzidan/iot_smartkittyflap/blob/main/Sample_Images/ALL/18731_ALL.png)

![Top Tier Engineering](https://github.com/lutzidan/iot_smartkittyflap/blob/main/Sample_Images/CAT/345_CAT.png)

![Top Tier Engineering](https://github.com/lutzidan/iot_smartkittyflap/blob/main/Images/s1.png)
![Top Tier Engineering](https://github.com/lutzidan/iot_smartkittyflap/blob/main/Images/s3.png)
![Top Tier Engineering](https://github.com/lutzidan/iot_smartkittyflap/blob/main/Images/s4.png)
![Top Tier Engineering](https://github.com/lutzidan/iot_smartkittyflap/blob/main/Images/s5.png)
![Top Tier Engineering](https://github.com/lutzidan/iot_smartkittyflap/blob/main/Images/s6.png)

## Anmerkungen
Der Code aus dem Video wurde leicht angepasst, um Daten zu simulieren. Das Problem war, dass die Katze in der Zeit der Bearbeitung keine Maus/Tier nach Hause brachte. Folglich müsste dieser Punkt in einer nächsten Version genauer angeschaut werden. 
Es wurden nicht alle Ressourcen wie Logs und Bilder in das Projekt hochgeladen. Jedoch sind von allen notwendigen Ressourcen eine repräsentative Menge vorhanden. Auf Anfrage stellen wir weitere Ressourcen gerne zur Verfügung. 

## Projekt Setup
### Installation
Zunächst muss ein Raspberry Pi inkl. Sense HAT eingerichtet werden. Diese Links könnten helfen: 
- [Get started with Raspberry Pi](https://projects.raspberrypi.org/en/pathways/getting-started-with-raspberry-pi)
- [Getting started with the Sense HAT](https://projects.raspberrypi.org/en/projects/getting-started-with-the-sense-hat)

Nun müssen einige Libraries installiert werden, bevor Sie loslegen können. Die wichtigsten sind hier aufgeführt:
- [Pandas](https://pandas.pydata.org/pandas-docs/stable/getting_started/install.html)
- [CV2](https://pypi.org/project/opencv-python/) für die Webcam
- [Paho MQTT](https://pypi.org/project/paho-mqtt/)
- [Twilio](https://www.twilio.com/docs/libraries/python)
- [TensorFlow Lite](https://www.tensorflow.org/lite/guide/python)
- [Node-RED](https://nodered.org/docs/getting-started/raspberrypi)
- [ngrok](https://ngrok.com/download) wurde für das Port-Forwarding verwendet. Siehe auch: [Access your Pi Away From your Home or Local Network](https://www.dexterindustries.com/howto/access-your-raspberry-pi-from-outside-your-home-or-local-network/)

### Einrichten von API Keys und notwendige Anpassungen
- Twilio: Geben Sie die API-Keys in `account_sid`, `auth_token` sowie Ihre Telefonnummer in `phone_number` im Python-Script `classify.py` an.
- OpenWeatherMap: Geben Sie die API-Keys im Node-RED-Flow `MQTT_Publish_WeatherData` im Node `Weather from owm-api` ein. API-Keys können Sie unter [https://openweathermap.org/api](https://openweathermap.org/api) einrichten.
- Sobald ngrok eingerichtet ist, erhalten Sie eine neue URL, unter welcher die Daten online verfügbar sind. Diese URL muss im Python-Script `classify.py` in `NGROK_PATH` eingesetzt werden.
- Der Pfad zur lokalen Ablage der cat.log-Datei auf dem Pi muss im Python-Script `classify.py` in `CATLOG_PATH` eingesetzt werden.
- Die Hierarchie der lokalen Logorder müsste wie folgt aussehen: `./logs/{ALL}/{Filename}` (`ALL = ALL/CAT/MOUSE/CAT_AND_MOUSE`)

### Projekt laufen lassen
Nachdem Sie alles eingerichtet haben, müssen Sie lediglich folgende Dinge ausführen:
1. Öffnen Sie `classify.py` und starten Sie das Python-Script. Nutzen Sie dafür beispielsweise die vorinstallierte Software "Thonny".
2. Öffnen Sie ein Terminal-Fenster und geben Sie `node-red` ein, um Node-RED zu starten. 
3. Öffnen Sie den Node-RED-Editor über die URL [http://localhost:1880/](http://localhost:1880/). Das Dashboard können Sie letztlich über [http://localhost:1880/ui](http://localhost:1880/ui) erreichen.
4. Importieren Sie die Flows von `Node_Red_Flows_SmartKittyFlap.json` und deployen Sie die Flows, nachdem Sie oben beschriebene API-Keys und weitere Einrichtungen abgeschlossen haben.
Sie haben das Projekt nun erfolgreich deployed und das Dashboard sollte Ihnen alle notwendigen Angaben liefern.

## Grobe Beschreibung des Inhalts
- Images: Enthält Fotos und Screenshots des Projektes
- Presentation: Enthält PowerPoint-Folien sowie zugehörige Videos der Präsentation
- Sample_Images: Enthält Fotos der Webcam als Beispieldaten
- Sample_Logs: Enthält Logs des Projektes als Beispieldaten
- Source-Code: Enthält die für die Applikation notwendigen Python-Scripte und Node-RED-Flows

### Source-Code
#### classify.py
Steuert die Webcam und published die Aufnahmen + Logs via ngrok sowie MQTT. Je nachdem, was durch die Image Classification erkannt wurde, wird ein Bild, Log und auch eine WhatsApp-Nachricht versendet. Das Script liefert auch die relevanten Daten für die Erstellung der Statistik-Grafiken im Node-RED-Dashboard.

Alle Methoden sind im Code dokumentiert.

#### image_classifier.py
Ein Standardscript für die Verwendung von Image-Classification mit TensorFlow Lite und Python.

#### Node_Red_Flows_CatProject.json
Enthält alle Flows, welche für Node-RED benötigt werden.

- Sense Hat Dashboard: Zeigt essenzielle performance-KPI's des Pi's im Dashboard an.
- MQTT_Publish_WeatherData: Liest die Wetterdaten via openweathermap-api und published diese in den Topics `weather`.
- MQTT_Subscribe_WeatherData: Subscribed mehrere `weather`-Topics und zeigt die Wetterdaten auf dem Dashboard an.
- MQTT_Subscribe_ImagesAndLogs: Subscribed mehrere `classify`-Topics und zeigt die Snapshots sowie letzten Logs im Dashboard an.
- MQTT_Subscribe_CatSymbol: Subscribed mehrere `classify`-Topics und ändert die Farbe der SVG-Katze entsprechend dem an, welches Topic eine Nachricht sendet. Die verwendete Funktion "convert to color" vergleicht dabei unter anderem, wie lange ein bestimmter Status schon gesetzt ist (mittels node-red context). Damit kann sichergestellt werden, dass der Farbstatus der SVG-Grafik, welche den "Zustand" des Katzentors simuliert, nach einer bestimmten Zeit wieder auf "ok" gesetzt wird, sorgt jedoch auch dafür, dass der Status sich bei "rot" nicht sofort ändert, nur weil bei einer Aufnahme womöglich einmal die falschen Objekte erkannt werden. 
- MQTT_Subscribe_Statistics: Subscribed mehrere `classify`-Topics und zeigt Statistische Grafiken im Dashboard an.
- MQTT_Subscribe_Table_detected objects: Subscribed das Topic `classify/allLog` und zeigt die erkannten Objekte inkl. Timestamp an der letzten 5 Logs an. Die letzten 5 Logs werden jeweils mittels "context" node-übergreifend gespeichert.

## Herausforderungen und "Way forward"
- NoiR PiCams gingen sehr schnell kaputt, weshalb wir auf eine USB-Webcam umgestiegen sind.
- Wetterresistenz bei der Installation muss beachtet werden
- Kamera hinter Fensterscheibe beeinträchtigt Performance und Bildqualität
- Die aufgenommenen Bilder waren zum trainieren eines eigenen Modelles mangelhaft. Die Aufnahme einer Katze sowie das "Fehlen" einer Maus oder anderer Beutetiere führten zu zu wenigen Daten, um ein Modell zu trainieren. Deshalb würde damit keine geeignete Performance des Modelles erzielt werden, weshalb auf ein Standardmodell von TensorFlow Lite zurückgegriffen wurde. 
- Das Senden von Bildern via Twilio war nur nach Port-Forwarding möglich (wodurch die Bilder online verfügbar wurden). Dies wurde mit ngrok gelöst.
-> Port-Forwarding-Lösungen wie remote.it könnte man in Zukunft näher betrachten.
- Der Livestream ins Node-RED-Dashboard liess sich nicht ohne weiteres Realisieren, weshalb wir mit den Snapshots gearbeitet haben.
- Auch Snapshots mussten online Verfügbar sein, dies wurde ebenfalls mit ngrok gelöst.

## Quellen
Tensorflow Code in Anlehnung an https://www.tensorflow.org/lite/examples/image_classification/overview
