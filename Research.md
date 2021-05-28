## Routes

- `/command`

  - commands appear to be form options sent as key and value pairs, key being the command and value being a parameter request
  - command options (as far as i have found)
    - `GETPRINTERSTATUS` Returns printer state, no form value
    - `PRINT=FILENAME.gcode` starts printing a file sent over network
    - `CANCEL=FILENAME.gcode` stops printing the file provided

- `/print_file_uploads`
  - Digilab seems to just be posting normal gcode files here
  - basic multipart form data sending

## Other Notes

- g3drem files only seem to be for usb transfers
- can accept gcode files

  - marlin flavor

- Below is from server state via `/commmand` + `d=GETPRINTERSTATUS`

```json
{
  "buildPlate_target_temperature": 0,
  "chamber_temperature": 0,
  "door_open": 0,
  "elaspedtime": 0,
  "error_code": 200,
  "extruder_target_temperature": 0,
  "fanSpeed": 0,
  "filament_type ": "PLA",
  "firmware_version": "v1.0_R03.06.06",
  "jobname": "D3_3DBenchy.gcode",
  "jobstatus": "preparing",
  "layer": 50,
  "message": "success",
  "networkBuild": 1,
  "platform_temperature": 0,
  "progress": 0,
  "remaining": 3072,
  "status": "busy",
  "temperature": 61,
  "totalTime": 3072
}
```

## g3drem files

- [Dremel3D20-Plugin](https://github.com/timmehtimmeh/Cura-Dremel-3D20-Plugin/blob/6ade070d48460260e85ffcf7eae3877376643845/plugins/Dremel3D20/Dremel3D20.py#L60)

## network printing examples

- this one is better -> https://github.com/Kriechi/Cura-DuetRRFPlugin/blob/4fccb8be1cc82a3e769b1d00ea91afbf8106e6d4/DuetRRFOutputDevice.py#L65
- https://github.com/alkaes/QidiPrint/blob/3c958c19b45c0b0a8901d14c7deae4e60e311cb6/QidiPrintPlugin.py#L27

## Plans?

- gonna hard code ips printing?
- write transmission program?
