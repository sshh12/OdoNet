

# Setup: Cameras

## A Camera Device

### Config

Add a camera to a node by editing
```javascript
...,
"devices": [],
...
```
to
```javascript
...,
"devices": [{
	"type": "CAMERA TYPE",
	"width": OPTIONAL (1920),
	"height": OPTIONAL (1080),
	"mode": OPTIONAL ("monitor", "stream"),
	"motion": OPTIONAL ('auto', 0-1000)
}],
...
```
Make sure to delete or edit the fields labeled `OPTIONAL`.

### Modes

* `stream` will constantly upload images to the root
* `monitor` will continuously capture images and calculate motion, when sufficient motion occurs, it will create an "event" and send that to the root.

## Camera Types

#### PiCamera

```javascript
{
	"type": "picamera"
}
```

#### FSWebcam

```javascript
{
	"type": "fswebcam",
}
```

#### OpenCV Camera

```javascript
{
	"type": "cvcamera",
	"url": 0
}
```

#### FTP Camera

```javascript
{
	"type": "ftpcamera",
	"username": "user",
	"password": "12345"
}
```

#### [Insteon 75790](https://www.amazon.com/Insteon-75790WH-Wireless-Security-Camera/dp/B0085HA0PA)

```javascript
{
	"type": "insteon-75790",
	"ip": "CAMERA IP",
	"username": "admin",
	"password": ""
}
```