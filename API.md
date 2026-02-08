# AI Audio Fingerprint Remover API Documentation

Base URL: `http://localhost:8000`

## Endpoints

### 1. Process Audio
Uploads an audio file, processes it to remove AI fingerprints/watermarks, and returns the processed file.

- **URL:** `/process`
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`

#### Request Parameters

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `file` | File | Yes | The audio file to process. Supported formats: `.wav`, `.mp3`, `.flac`, `.aiff`, `.m4a`. | - |
| `level` | String | No | Processing intensity level. Options: `gentle`, `balanced`, `aggressive`, `extreme`. | `balanced` |
| `aggressive_mode` | Boolean | No | Enable legacy aggressive mode. | `false` |

#### Success Response
- **Code:** 200 OK
- **Content-Type:** `audio/wav` (or other audio types) - actually `application/octet-stream`
- **Content:** The processed audio binary.

#### Error Responses
- **Code:** 400 Bad Request
  - Content: `{"detail": "No filename provided"}`
  - Content: `{"detail": "Unsupported file extension: .xyz"}`
- **Code:** 500 Internal Server Error
  - Content: `{"detail": "Error processing file: ..."}`

#### Example Usage (cURL)
```bash
curl -X POST "http://localhost:8000/process" \
  -F "file=@/path/to/your/audio.mp3" \
  -F "level=aggressive"
```

#### Example Usage (JavaScript/Fetch)
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('level', 'balanced');

const response = await fetch('http://localhost:8000/process', {
  method: 'POST',
  body: formData,
});

if (response.ok) {
  const blob = await response.blob();
  // Handle the downloaded file blob
} else {
  console.error('Upload failed');
}
```

### 2. Health Check
Check if the API is running.

- **URL:** `/`
- **Method:** `GET`

#### Response
- **Code:** 200 OK
- **Content:** `{"message": "AI Audio Fingerprint Remover API is running"}`
