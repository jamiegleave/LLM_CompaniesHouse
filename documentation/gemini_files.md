[![Gemini API](https://ai.google.dev/_static/googledevai/images/lockup-new.svg)](/)

`/`

- [English](https://ai.google.dev/api/files#image)
- [Deutsch](https://ai.google.dev/api/files?hl=de#image)
- [Español – América Latina](https://ai.google.dev/api/files?hl=es-419#image)
- [Français](https://ai.google.dev/api/files?hl=fr#image)
- [Indonesia](https://ai.google.dev/api/files?hl=id#image)
- [Italiano](https://ai.google.dev/api/files?hl=it#image)
- [Polski](https://ai.google.dev/api/files?hl=pl#image)
- [Português – Brasil](https://ai.google.dev/api/files?hl=pt-br#image)
- [Shqip](https://ai.google.dev/api/files?hl=sq#image)
- [Tiếng Việt](https://ai.google.dev/api/files?hl=vi#image)
- [Türkçe](https://ai.google.dev/api/files?hl=tr#image)
- [Русский](https://ai.google.dev/api/files?hl=ru#image)
- [עברית](https://ai.google.dev/api/files?hl=he#image)
- [العربيّة](https://ai.google.dev/api/files?hl=ar#image)
- [فارسی](https://ai.google.dev/api/files?hl=fa#image)
- [हिंदी](https://ai.google.dev/api/files?hl=hi#image)
- [বাংলা](https://ai.google.dev/api/files?hl=bn#image)
- [ภาษาไทย](https://ai.google.dev/api/files?hl=th#image)
- [中文 – 简体](https://ai.google.dev/api/files?hl=zh-cn#image)
- [中文 – 繁體](https://ai.google.dev/api/files?hl=zh-tw#image)
- [日本語](https://ai.google.dev/api/files?hl=ja#image)
- [한국어](https://ai.google.dev/api/files?hl=ko#image)

[Sign in](https://ai.google.dev/_d/signin?continue=https%3A%2F%2Fai.google.dev%2Fapi%2Ffiles%23image&prompt=select_account)

- On this page
- [Method: media.upload](#method:-media.upload)
  - [Endpoint](#endpoint)
  - [Request body](#request-body)
  - [Example request](#example-request)
  - [Response body](#response-body)
- [Method: files.get](#method:-files.get)
  - [Endpoint](#endpoint_1)
  - [Path parameters](#path-parameters)
  - [Request body](#request-body_1)
  - [Example request](#example-request_1)
  - [Response body](#response-body_1)
- [Method: files.list](#method:-files.list)
  - [Endpoint](#endpoint_2)
  - [Query parameters](#query-parameters)
  - [Request body](#request-body_2)
  - [Example request](#example-request_2)
  - [Response body](#response-body_2)
- [Method: files.delete](#method:-files.delete)
  - [Endpoint](#endpoint_3)
  - [Path parameters](#path-parameters_1)
  - [Request body](#request-body_3)
  - [Example request](#example-request_3)
  - [Response body](#response-body_3)
- [REST Resource: files](#rest-resource:-files)
- [Resource: File](#File)
- [VideoMetadata](#VideoMetadata)
- [State](#State)
- [Status](#Status)

Gemini 2.0 Flash Experimental is now available! [Learn more](https://developers.googleblog.com/en/the-next-chapter-of-the-gemini-era-for-developers/)

- [Home](https://ai.google.dev/)
- [Gemini API](https://ai.google.dev/gemini-api)
- [Models](https://ai.google.dev/gemini-api/docs)
- [API Reference](https://ai.google.dev/api)

Was this helpful?



 Send feedback



# Using files

- On this page
- [Method: media.upload](#method:-media.upload)
  - [Endpoint](#endpoint)
  - [Request body](#request-body)
  - [Example request](#example-request)
  - [Response body](#response-body)
- [Method: files.get](#method:-files.get)
  - [Endpoint](#endpoint_1)
  - [Path parameters](#path-parameters)
  - [Request body](#request-body_1)
  - [Example request](#example-request_1)
  - [Response body](#response-body_1)
- [Method: files.list](#method:-files.list)
  - [Endpoint](#endpoint_2)
  - [Query parameters](#query-parameters)
  - [Request body](#request-body_2)
  - [Example request](#example-request_2)
  - [Response body](#response-body_2)
- [Method: files.delete](#method:-files.delete)
  - [Endpoint](#endpoint_3)
  - [Path parameters](#path-parameters_1)
  - [Request body](#request-body_3)
  - [Example request](#example-request_3)
  - [Response body](#response-body_3)
- [REST Resource: files](#rest-resource:-files)
- [Resource: File](#File)
- [VideoMetadata](#VideoMetadata)
- [State](#State)
- [Status](#Status)

The Gemini API supports uploading media files separately from the prompt input, allowing your media to be reused across multiple requests and multiple prompts. For more details, check out the [Prompting with media](https://ai.google.dev/gemini-api/docs/prompting_with_media) guide.

## Method: media.upload

- [Endpoint](#body.HTTP_TEMPLATE)
- [Request body](#body.request_body)
  - [JSON representation](#body.request_body.SCHEMA_REPRESENTATION)
- [Response body](#body.response_body)
  - [JSON representation](#body.CreateFileResponse.SCHEMA_REPRESENTATION)
- [Example request](#body.codeSnippets)
  - [Image](#body.codeSnippets.group)
  - [Audio](#body.codeSnippets.group_1)
  - [Text](#body.codeSnippets.group_2)
  - [Video](#body.codeSnippets.group_3)
  - [PDF](#body.codeSnippets.group_4)

Creates a `File`.

### Endpoint

- Upload URI, for media upload requests:


post

https://generativelanguage.googleapis.com/upload/v1beta/files


- Metadata URI, for metadata-only requests:


post

https://generativelanguage.googleapis.com/v1beta/files


### Request body

The request body contains data with the following structure:

Fields

`file``object (File)`

Optional. Metadata for the file to create.

### Example request

[Image](#image)[Audio](#audio)[Text](#text)[Video](#video)[PDF](#pdf)More

[Python](#python)[Node.js](#node.js)[Go](#go)[Shell](#shell)More

```
import google.generativeai as genai

myfile = genai.upload_file(media / "Cajun_instruments.jpg")
print(f"{myfile=}")

model = genai.GenerativeModel("gemini-1.5-flash")
result = model.generate_content(
    [myfile, "\n\n", "Can you tell me about the instruments in this photo?"]
)
print(f"{result.text=}")
files.py
```

```
// Make sure to include these imports:
// import { GoogleAIFileManager } from "@google/generative-ai/server";
// import { GoogleGenerativeAI } from "@google/generative-ai";
const fileManager = new GoogleAIFileManager(process.env.API_KEY);

const uploadResult = await fileManager.uploadFile(
  `${mediaPath}/jetpack.jpg`,
  {
    mimeType: "image/jpeg",
    displayName: "Jetpack drawing",
  },
);
// View the response.
console.log(
  `Uploaded file ${uploadResult.file.displayName} as: ${uploadResult.file.uri}`,
);

const genAI = new GoogleGenerativeAI(process.env.API_KEY);
const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
const result = await model.generateContent([\
  "Tell me about this image.",\
  {\
    fileData: {\
      fileUri: uploadResult.file.uri,\
      mimeType: uploadResult.file.mimeType,\
    },\
  },\
]);
console.log(result.response.text());
files.js
```

```
file, err := client.UploadFileFromPath(ctx, filepath.Join(testDataDir, "Cajun_instruments.jpg"), nil)
if err != nil {
	log.Fatal(err)
}
defer client.DeleteFile(ctx, file.Name)

model := client.GenerativeModel("gemini-1.5-flash")
resp, err := model.GenerateContent(ctx,
	genai.FileData{URI: file.URI},
	genai.Text("Can you tell me about the instruments in this photo?"))
if err != nil {
	log.Fatal(err)
}

printResponse(resp)
docs-snippets_test.go
```

```
MIME_TYPE=$(file -b --mime-type "${IMG_PATH_2}")
NUM_BYTES=$(wc -c < "${IMG_PATH_2}")
DISPLAY_NAME=TEXT

tmp_header_file=upload-header.tmp

# Initial resumable request defining metadata.
# The upload url is in the response headers dump them to a file.
curl "${BASE_URL}/upload/v1beta/files?key=${GOOGLE_API_KEY}" \
  -D upload-header.tmp \
  -H "X-Goog-Upload-Protocol: resumable" \
  -H "X-Goog-Upload-Command: start" \
  -H "X-Goog-Upload-Header-Content-Length: ${NUM_BYTES}" \
  -H "X-Goog-Upload-Header-Content-Type: ${MIME_TYPE}" \
  -H "Content-Type: application/json" \
  -d "{'file': {'display_name': '${DISPLAY_NAME}'}}" 2> /dev/null

upload_url=$(grep -i "x-goog-upload-url: " "${tmp_header_file}" | cut -d" " -f2 | tr -d "\r")
rm "${tmp_header_file}"

# Upload the actual bytes.
curl "${upload_url}" \
  -H "Content-Length: ${NUM_BYTES}" \
  -H "X-Goog-Upload-Offset: 0" \
  -H "X-Goog-Upload-Command: upload, finalize" \
  --data-binary "@${IMG_PATH_2}" 2> /dev/null > file_info.json

file_uri=$(jq ".file.uri" file_info.json)
echo file_uri=$file_uri

# Now generate content using that file
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=$GOOGLE_API_KEY" \
    -H 'Content-Type: application/json' \
    -X POST \
    -d '{
      "contents": [{\
        "parts":[\
          {"text": "Can you tell me about the instruments in this photo?"},\
          {"file_data":\
            {"mime_type": "image/jpeg",\
            "file_uri": '$file_uri'}\
        }]\
        }]
       }' 2> /dev/null > response.json

cat response.json
echo

jq ".candidates[].content.parts[].text" response.json
files.sh
```

[Python](#python)[Node.js](#node.js)[Go](#go)[Shell](#shell)More

```
import google.generativeai as genai

myfile = genai.upload_file(media / "sample.mp3")
print(f"{myfile=}")

model = genai.GenerativeModel("gemini-1.5-flash")
result = model.generate_content([myfile, "Describe this audio clip"])
print(f"{result.text=}")
files.py
```

```
// Make sure to include these imports:
// import { GoogleAIFileManager, FileState } from "@google/generative-ai/server";
// import { GoogleGenerativeAI } from "@google/generative-ai";
const fileManager = new GoogleAIFileManager(process.env.API_KEY);

const uploadResult = await fileManager.uploadFile(
  `${mediaPath}/samplesmall.mp3`,
  {
    mimeType: "audio/mp3",
    displayName: "Audio sample",
  },
);

let file = await fileManager.getFile(uploadResult.file.name);
while (file.state === FileState.PROCESSING) {
  process.stdout.write(".");
  // Sleep for 10 seconds
  await new Promise((resolve) => setTimeout(resolve, 10_000));
  // Fetch the file from the API again
  file = await fileManager.getFile(uploadResult.file.name);
}

if (file.state === FileState.FAILED) {
  throw new Error("Audio processing failed.");
}

// View the response.
console.log(
  `Uploaded file ${uploadResult.file.displayName} as: ${uploadResult.file.uri}`,
);

const genAI = new GoogleGenerativeAI(process.env.API_KEY);
const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
const result = await model.generateContent([\
  "Tell me about this audio clip.",\
  {\
    fileData: {\
      fileUri: uploadResult.file.uri,\
      mimeType: uploadResult.file.mimeType,\
    },\
  },\
]);
console.log(result.response.text());
files.js
```

```
file, err := client.UploadFileFromPath(ctx, filepath.Join(testDataDir, "sample.mp3"), nil)
if err != nil {
	log.Fatal(err)
}
defer client.DeleteFile(ctx, file.Name)

model := client.GenerativeModel("gemini-1.5-flash")
resp, err := model.GenerateContent(ctx,
	genai.FileData{URI: file.URI},
	genai.Text("Describe this audio clip"))
if err != nil {
	log.Fatal(err)
}

printResponse(resp)
docs-snippets_test.go
```

```
MIME_TYPE=$(file -b --mime-type "${AUDIO_PATH}")
NUM_BYTES=$(wc -c < "${AUDIO_PATH}")
DISPLAY_NAME=AUDIO

tmp_header_file=upload-header.tmp

# Initial resumable request defining metadata.
# The upload url is in the response headers dump them to a file.
curl "${BASE_URL}/upload/v1beta/files?key=${GOOGLE_API_KEY}" \
  -D upload-header.tmp \
  -H "X-Goog-Upload-Protocol: resumable" \
  -H "X-Goog-Upload-Command: start" \
  -H "X-Goog-Upload-Header-Content-Length: ${NUM_BYTES}" \
  -H "X-Goog-Upload-Header-Content-Type: ${MIME_TYPE}" \
  -H "Content-Type: application/json" \
  -d "{'file': {'display_name': '${DISPLAY_NAME}'}}" 2> /dev/null

upload_url=$(grep -i "x-goog-upload-url: " "${tmp_header_file}" | cut -d" " -f2 | tr -d "\r")
rm "${tmp_header_file}"

# Upload the actual bytes.
curl "${upload_url}" \
  -H "Content-Length: ${NUM_BYTES}" \
  -H "X-Goog-Upload-Offset: 0" \
  -H "X-Goog-Upload-Command: upload, finalize" \
  --data-binary "@${AUDIO_PATH}" 2> /dev/null > file_info.json

file_uri=$(jq ".file.uri" file_info.json)
echo file_uri=$file_uri

# Now generate content using that file
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=$GOOGLE_API_KEY" \
    -H 'Content-Type: application/json' \
    -X POST \
    -d '{
      "contents": [{\
        "parts":[\
          {"text": "Describe this audio clip"},\
          {"file_data":{"mime_type": "audio/mp3", "file_uri": '$file_uri'}}]\
        }]
       }' 2> /dev/null > response.json

cat response.json
echo

jq ".candidates[].content.parts[].text" response.json
files.sh
```

[Python](#python)[Node.js](#node.js)[Go](#go)[Shell](#shell)More

```
import google.generativeai as genai

myfile = genai.upload_file(media / "poem.txt")
print(f"{myfile=}")

model = genai.GenerativeModel("gemini-1.5-flash")
result = model.generate_content(
    [myfile, "\n\n", "Can you add a few more lines to this poem?"]
)
print(f"{result.text=}")
files.py
```

```
// Make sure to include these imports:
// import { GoogleAIFileManager } from "@google/generative-ai/server";
// import { GoogleGenerativeAI } from "@google/generative-ai";
const fileManager = new GoogleAIFileManager(process.env.API_KEY);

const uploadResult = await fileManager.uploadFile(`${mediaPath}/a11.txt`, {
  mimeType: "text/plain",
  displayName: "Apollo 11",
});
// View the response.
console.log(
  `Uploaded file ${uploadResult.file.displayName} as: ${uploadResult.file.uri}`,
);

const genAI = new GoogleGenerativeAI(process.env.API_KEY);
const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
const result = await model.generateContent([\
  "Transcribe the first few sentences of this document.",\
  {\
    fileData: {\
      fileUri: uploadResult.file.uri,\
      mimeType: uploadResult.file.mimeType,\
    },\
  },\
]);
console.log(result.response.text());
files.js
```

```
// Set MIME type explicitly for text files - the service may have difficulty
// distingushing between different MIME types of text files automatically.
file, err := client.UploadFileFromPath(ctx, filepath.Join(testDataDir, "poem.txt"), nil)
if err != nil {
	log.Fatal(err)
}
defer client.DeleteFile(ctx, file.Name)

model := client.GenerativeModel("gemini-1.5-flash")
resp, err := model.GenerateContent(ctx,
	genai.FileData{URI: file.URI},
	genai.Text("Can you add a few more lines to this poem?"))
if err != nil {
	log.Fatal(err)
}

printResponse(resp)
docs-snippets_test.go
```

```
MIME_TYPE=$(file -b --mime-type "${TEXT_PATH}")
NUM_BYTES=$(wc -c < "${TEXT_PATH}")
DISPLAY_NAME=TEXT

tmp_header_file=upload-header.tmp

# Initial resumable request defining metadata.
# The upload url is in the response headers dump them to a file.
curl "${BASE_URL}/upload/v1beta/files?key=${GOOGLE_API_KEY}" \
  -D upload-header.tmp \
  -H "X-Goog-Upload-Protocol: resumable" \
  -H "X-Goog-Upload-Command: start" \
  -H "X-Goog-Upload-Header-Content-Length: ${NUM_BYTES}" \
  -H "X-Goog-Upload-Header-Content-Type: ${MIME_TYPE}" \
  -H "Content-Type: application/json" \
  -d "{'file': {'display_name': '${DISPLAY_NAME}'}}" 2> /dev/null

upload_url=$(grep -i "x-goog-upload-url: " "${tmp_header_file}" | cut -d" " -f2 | tr -d "\r")
rm "${tmp_header_file}"

# Upload the actual bytes.
curl "${upload_url}" \
  -H "Content-Length: ${NUM_BYTES}" \
  -H "X-Goog-Upload-Offset: 0" \
  -H "X-Goog-Upload-Command: upload, finalize" \
  --data-binary "@${TEXT_PATH}" 2> /dev/null > file_info.json

file_uri=$(jq ".file.uri" file_info.json)
echo file_uri=$file_uri

# Now generate content using that file
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=$GOOGLE_API_KEY" \
    -H 'Content-Type: application/json' \
    -X POST \
    -d '{
      "contents": [{\
        "parts":[\
          {"text": "Can you add a few more lines to this poem?"},\
          {"file_data":{"mime_type": "text/plain", "file_uri": '$file_uri'}}]\
        }]
       }' 2> /dev/null > response.json

cat response.json
echo

jq ".candidates[].content.parts[].text" response.json

name=$(jq ".file.name" file_info.json)
# Get the file of interest to check state
curl https://generativelanguage.googleapis.com/v1beta/files/$name > file_info.json
# Print some information about the file you got
name=$(jq ".file.name" file_info.json)
echo name=$name
file_uri=$(jq ".file.uri" file_info.json)
echo file_uri=$file_uri

curl --request "DELETE" https://generativelanguage.googleapis.com/v1beta/files/$name?key=$GOOGLE_API_KEY

files.sh
```

[Python](#python)[Node.js](#node.js)[Go](#go)[Shell](#shell)More

```
import google.generativeai as genai

import time

# Video clip (CC BY 3.0) from https://peach.blender.org/download/
myfile = genai.upload_file(media / "Big_Buck_Bunny.mp4")
print(f"{myfile=}")

# Videos need to be processed before you can use them.
while myfile.state.name == "PROCESSING":
    print("processing video...")
    time.sleep(5)
    myfile = genai.get_file(myfile.name)

model = genai.GenerativeModel("gemini-1.5-flash")
result = model.generate_content([myfile, "Describe this video clip"])
print(f"{result.text=}")
files.py
```

```
// Make sure to include these imports:
// import { GoogleAIFileManager, FileState } from "@google/generative-ai/server";
// import { GoogleGenerativeAI } from "@google/generative-ai";
const fileManager = new GoogleAIFileManager(process.env.API_KEY);

const uploadResult = await fileManager.uploadFile(
  `${mediaPath}/Big_Buck_Bunny.mp4`,
  {
    mimeType: "video/mp4",
    displayName: "Big Buck Bunny",
  },
);

let file = await fileManager.getFile(uploadResult.file.name);
while (file.state === FileState.PROCESSING) {
  process.stdout.write(".");
  // Sleep for 10 seconds
  await new Promise((resolve) => setTimeout(resolve, 10_000));
  // Fetch the file from the API again
  file = await fileManager.getFile(uploadResult.file.name);
}

if (file.state === FileState.FAILED) {
  throw new Error("Video processing failed.");
}

// View the response.
console.log(
  `Uploaded file ${uploadResult.file.displayName} as: ${uploadResult.file.uri}`,
);

const genAI = new GoogleGenerativeAI(process.env.API_KEY);
const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
const result = await model.generateContent([\
  "Tell me about this video.",\
  {\
    fileData: {\
      fileUri: uploadResult.file.uri,\
      mimeType: uploadResult.file.mimeType,\
    },\
  },\
]);
console.log(result.response.text());
files.js
```

```
file, err := client.UploadFileFromPath(ctx, filepath.Join(testDataDir, "earth.mp4"), nil)
if err != nil {
	log.Fatal(err)
}
defer client.DeleteFile(ctx, file.Name)

// Videos need to be processed before you can use them.
for file.State == genai.FileStateProcessing {
	log.Printf("processing %s", file.Name)
	time.Sleep(5 * time.Second)
	var err error
	if file, err = client.GetFile(ctx, file.Name); err != nil {
		log.Fatal(err)
	}
}
if file.State != genai.FileStateActive {
	log.Fatalf("uploaded file has state %s, not active", file.State)
}

model := client.GenerativeModel("gemini-1.5-flash")
resp, err := model.GenerateContent(ctx,
	genai.FileData{URI: file.URI},
	genai.Text("Describe this video clip"))
if err != nil {
	log.Fatal(err)
}

printResponse(resp)
docs-snippets_test.go
```

```
MIME_TYPE=$(file -b --mime-type "${VIDEO_PATH}")
NUM_BYTES=$(wc -c < "${VIDEO_PATH}")
DISPLAY_NAME=VIDEO_PATH

# Initial resumable request defining metadata.
# The upload url is in the response headers dump them to a file.
curl "${BASE_URL}/upload/v1beta/files?key=${GOOGLE_API_KEY}" \
  -D upload-header.tmp \
  -H "X-Goog-Upload-Protocol: resumable" \
  -H "X-Goog-Upload-Command: start" \
  -H "X-Goog-Upload-Header-Content-Length: ${NUM_BYTES}" \
  -H "X-Goog-Upload-Header-Content-Type: ${MIME_TYPE}" \
  -H "Content-Type: application/json" \
  -d "{'file': {'display_name': '${DISPLAY_NAME}'}}" 2> /dev/null

upload_url=$(grep -i "x-goog-upload-url: " "${tmp_header_file}" | cut -d" " -f2 | tr -d "\r")
rm "${tmp_header_file}"

# Upload the actual bytes.
curl "${upload_url}" \
  -H "Content-Length: ${NUM_BYTES}" \
  -H "X-Goog-Upload-Offset: 0" \
  -H "X-Goog-Upload-Command: upload, finalize" \
  --data-binary "@${VIDEO_PATH}" 2> /dev/null > file_info.json

file_uri=$(jq ".file.uri" file_info.json)
echo file_uri=$file_uri

state=$(jq ".file.state" file_info.json)
echo state=$state

# Ensure the state of the video is 'ACTIVE'
while [[ "($state)" = *"PROCESSING"* ]];
do
  echo "Processing video..."
  sleep 5
  # Get the file of interest to check state
  curl https://generativelanguage.googleapis.com/v1beta/files/$name > file_info.json
  state=$(jq ".file.state" file_info.json)
done

# Now generate content using that file
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=$GOOGLE_API_KEY" \
    -H 'Content-Type: application/json' \
    -X POST \
    -d '{
      "contents": [{\
        "parts":[\
          {"text": "Describe this video clip"},\
          {"file_data":{"mime_type": "video/mp4", "file_uri": '$file_uri'}}]\
        }]
       }' 2> /dev/null > response.json

cat response.json
echo

jq ".candidates[].content.parts[].text" response.json
files.sh
```

[Python](#python)More

```
import google.generativeai as genai

model = genai.GenerativeModel("gemini-1.5-flash")
sample_pdf = genai.upload_file(media / "test.pdf")
response = model.generate_content(["Give me a summary of this pdf file.", sample_pdf])
print(response.text)
files.py
```

### Response body

Response for `media.upload`.

If successful, the response body contains data with the following structure:

Fields

`file``object (File)`

Metadata for the created file.

| JSON representation |
| --- |
| ```<br>{<br>  "file": {<br>    object (File)<br>  }<br>}<br>``` |

## Method: files.get

- [Endpoint](#body.HTTP_TEMPLATE)
- [Path parameters](#body.PATH_PARAMETERS)
- [Request body](#body.request_body)
- [Response body](#body.response_body)
- [Example request](#body.codeSnippets)
  - [Basic](#body.codeSnippets.group)

Gets the metadata for the given `File`.

### Endpoint

get

https://generativelanguage.googleapis.com/v1beta/{name=files/\*}


### Path parameters

`name``string`

Required. The name of the `File` to get. Example: `files/abc-123` It takes the form `files/{file}`.

### Request body

The request body must be empty.

### Example request

[Python](#python)[Node.js](#node.js)[Go](#go)[Shell](#shell)More

```
import google.generativeai as genai

myfile = genai.upload_file(media / "poem.txt")
file_name = myfile.name
print(file_name)  # "files/*"

myfile = genai.get_file(file_name)
print(myfile)
files.py
```

```
// Make sure to include these imports:
// import { GoogleAIFileManager } from "@google/generative-ai/server";
const fileManager = new GoogleAIFileManager(process.env.API_KEY);

const uploadResponse = await fileManager.uploadFile(
  `${mediaPath}/jetpack.jpg`,
  {
    mimeType: "image/jpeg",
    displayName: "Jetpack drawing",
  },
);

// Get the previously uploaded file's metadata.
const getResponse = await fileManager.getFile(uploadResponse.file.name);

// View the response.
console.log(
  `Retrieved file ${getResponse.displayName} as ${getResponse.uri}`,
);
files.js
```

```
file, err := client.UploadFileFromPath(ctx, filepath.Join(testDataDir, "personWorkingOnComputer.jpg"), nil)
if err != nil {
	log.Fatal(err)
}
defer client.DeleteFile(ctx, file.Name)

gotFile, err := client.GetFile(ctx, file.Name)
if err != nil {
	log.Fatal(err)
}
fmt.Println("Got file:", gotFile.Name)

model := client.GenerativeModel("gemini-1.5-flash")
resp, err := model.GenerateContent(ctx,
	genai.FileData{URI: file.URI},
	genai.Text("Describe this image"))
if err != nil {
	log.Fatal(err)
}

printResponse(resp)
docs-snippets_test.go
```

```
name=$(jq ".file.name" file_info.json)
# Get the file of interest to check state
curl https://generativelanguage.googleapis.com/v1beta/files/$name > file_info.json
# Print some information about the file you got
name=$(jq ".file.name" file_info.json)
echo name=$name
file_uri=$(jq ".file.uri" file_info.json)
echo file_uri=$file_uri
files.sh
```

### Response body

If successful, the response body contains an instance of `File`.

## Method: files.list

- [Endpoint](#body.HTTP_TEMPLATE)
- [Query parameters](#body.QUERY_PARAMETERS)
- [Request body](#body.request_body)
- [Response body](#body.response_body)
  - [JSON representation](#body.ListFilesResponse.SCHEMA_REPRESENTATION)
- [Example request](#body.codeSnippets)
  - [Basic](#body.codeSnippets.group)

Lists the metadata for `File` s owned by the requesting project.

### Endpoint

get

https://generativelanguage.googleapis.com/v1beta/files


### Query parameters

`pageSize``integer`

Optional. Maximum number of `File` s to return per page. If unspecified, defaults to 10. Maximum `pageSize` is 100.

`pageToken``string`

Optional. A page token from a previous `files.list` call.

### Request body

The request body must be empty.

### Example request

[Python](#python)[Node.js](#node.js)[Go](#go)[Shell](#shell)More

```
import google.generativeai as genai

print("My files:")
for f in genai.list_files():
    print("  ", f.name)
files.py
```

```
// Make sure to include these imports:
// import { GoogleAIFileManager } from "@google/generative-ai/server";
const fileManager = new GoogleAIFileManager(process.env.API_KEY);

const listFilesResponse = await fileManager.listFiles();

// View the response.
for (const file of listFilesResponse.files) {
  console.log(`name: ${file.name} | display name: ${file.displayName}`);
}
files.js
```

```
iter := client.ListFiles(ctx)
for {
	ifile, err := iter.Next()
	if err == iterator.Done {
		break
	}
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println(ifile.Name)
}
docs-snippets_test.go
```

```
echo "My files: "

curl "https://generativelanguage.googleapis.com/v1beta/files?key=$GOOGLE_API_KEY"
files.sh
```

### Response body

Response for `files.list`.

If successful, the response body contains data with the following structure:

Fields

`files[]``object (File)`

The list of `File` s.

`nextPageToken``string`

A token that can be sent as a `pageToken` into a subsequent `files.list` call.

| JSON representation |
| --- |
| ```<br>{<br>  "files": [<br>    {<br>      object (File)<br>    }<br>  ],<br>  "nextPageToken": string<br>}<br>``` |

## Method: files.delete

- [Endpoint](#body.HTTP_TEMPLATE)
- [Path parameters](#body.PATH_PARAMETERS)
- [Request body](#body.request_body)
- [Response body](#body.response_body)
- [Example request](#body.codeSnippets)
  - [Basic](#body.codeSnippets.group)

Deletes the `File`.

### Endpoint

delete

https://generativelanguage.googleapis.com/v1beta/{name=files/\*}


### Path parameters

`name``string`

Required. The name of the `File` to delete. Example: `files/abc-123` It takes the form `files/{file}`.

### Request body

The request body must be empty.

### Example request

[Python](#python)[Node.js](#node.js)[Go](#go)[Shell](#shell)More

```
import google.generativeai as genai

myfile = genai.upload_file(media / "poem.txt")

myfile.delete()

try:
    # Error.
    model = genai.GenerativeModel("gemini-1.5-flash")
    result = model.generate_content([myfile, "Describe this file."])
except google.api_core.exceptions.PermissionDenied:
    pass
files.py
```

```
// Make sure to include these imports:
// import { GoogleAIFileManager } from "@google/generative-ai/server";
const fileManager = new GoogleAIFileManager(process.env.API_KEY);

const uploadResult = await fileManager.uploadFile(
  `${mediaPath}/jetpack.jpg`,
  {
    mimeType: "image/jpeg",
    displayName: "Jetpack drawing",
  },
);

// Delete the file.
await fileManager.deleteFile(uploadResult.file.name);

console.log(`Deleted ${uploadResult.file.displayName}`);
files.js
```

```
file, err := client.UploadFileFromPath(ctx, filepath.Join(testDataDir, "personWorkingOnComputer.jpg"), nil)
if err != nil {
	log.Fatal(err)
}
defer client.DeleteFile(ctx, file.Name)

gotFile, err := client.GetFile(ctx, file.Name)
if err != nil {
	log.Fatal(err)
}
fmt.Println("Got file:", gotFile.Name)

model := client.GenerativeModel("gemini-1.5-flash")
resp, err := model.GenerateContent(ctx,
	genai.FileData{URI: file.URI},
	genai.Text("Describe this image"))
if err != nil {
	log.Fatal(err)
}

printResponse(resp)
docs-snippets_test.go
```

```
curl --request "DELETE" https://generativelanguage.googleapis.com/v1beta/files/$name?key=$GOOGLE_API_KEY
files.sh
```

### Response body

If successful, the response body is empty.

## REST Resource: files

- [Resource: File](#File)
  - [JSON representation](#File.SCHEMA_REPRESENTATION)
- [VideoMetadata](#VideoMetadata)
  - [JSON representation](#VideoMetadata.SCHEMA_REPRESENTATION)
- [State](#State)
- [Status](#Status)
  - [JSON representation](#Status.SCHEMA_REPRESENTATION)
- [Methods](#METHODS_SUMMARY)

## Resource: File

A file uploaded to the API.

Fields

`name``string`

Immutable. Identifier. The `File` resource name. The ID (name excluding the "files/" prefix) can contain up to 40 characters that are lowercase alphanumeric or dashes (-). The ID cannot start or end with a dash. If the name is empty on create, a unique name will be generated. Example: `files/123-456`

`displayName``string`

Optional. The human-readable display name for the `File`. The display name must be no more than 512 characters in length, including spaces. Example: "Welcome Image"

`mimeType``string`

Output only. MIME type of the file.

`sizeBytes``string (int64 format)`

Output only. Size of the file in bytes.

`createTime``string (Timestamp format)`

Output only. The timestamp of when the `File` was created.

A timestamp in RFC3339 UTC "Zulu" format, with nanosecond resolution and up to nine fractional digits. Examples: `"2014-10-02T15:01:23Z"` and `"2014-10-02T15:01:23.045123456Z"`.

`updateTime``string (Timestamp format)`

Output only. The timestamp of when the `File` was last updated.

A timestamp in RFC3339 UTC "Zulu" format, with nanosecond resolution and up to nine fractional digits. Examples: `"2014-10-02T15:01:23Z"` and `"2014-10-02T15:01:23.045123456Z"`.

`expirationTime``string (Timestamp format)`

Output only. The timestamp of when the `File` will be deleted. Only set if the `File` is scheduled to expire.

A timestamp in RFC3339 UTC "Zulu" format, with nanosecond resolution and up to nine fractional digits. Examples: `"2014-10-02T15:01:23Z"` and `"2014-10-02T15:01:23.045123456Z"`.

`sha256Hash``string (bytes format)`

Output only. SHA-256 hash of the uploaded bytes.

A base64-encoded string.

`uri``string`

Output only. The uri of the `File`.

`state``enum (State)`

Output only. Processing state of the File.

`error``object (Status)`

Output only. Error status if File processing failed.

Union field `metadata`. Metadata for the File. `metadata` can be only one of the following:

`videoMetadata``object (VideoMetadata)`

Output only. Metadata for a video.

| JSON representation |
| --- |
| ```<br>{<br>  "name": string,<br>  "displayName": string,<br>  "mimeType": string,<br>  "sizeBytes": string,<br>  "createTime": string,<br>  "updateTime": string,<br>  "expirationTime": string,<br>  "sha256Hash": string,<br>  "uri": string,<br>  "state": enum (State),<br>  "error": {<br>    object (Status)<br>  },<br>  // Union field metadata can be only one of the following:<br>  "videoMetadata": {<br>    object (VideoMetadata)<br>  }<br>  // End of list of possible types for union field metadata.<br>}<br>``` |

## VideoMetadata

Metadata for a video `File`.

Fields

`videoDuration``string (Duration format)`

Duration of the video.

A duration in seconds with up to nine fractional digits, ending with ' `s`'. Example: `"3.5s"`.

| JSON representation |
| --- |
| ```<br>{<br>  "videoDuration": string<br>}<br>``` |

## State

States for the lifecycle of a File.

| Enums |
| --- |
| `STATE_UNSPECIFIED` | The default value. This value is used if the state is omitted. |
| `PROCESSING` | File is being processed and cannot be used for inference yet. |
| `ACTIVE` | File is processed and available for inference. |
| `FAILED` | File failed processing. |

## Status

The `Status` type defines a logical error model that is suitable for different programming environments, including REST APIs and RPC APIs. It is used by [gRPC](https://github.com/grpc). Each `Status` message contains three pieces of data: error code, error message, and error details.

You can find out more about this error model and how to work with it in the [API Design Guide](https://cloud.google.com/apis/design/errors).

Fields

`code``integer`

The status code, which should be an enum value of `google.rpc.Code`.

`message``string`

A developer-facing error message, which should be in English. Any user-facing error message should be localized and sent in the `google.rpc.Status.details` field, or localized by the client.

`details[]``object`

A list of messages that carry the error details. There is a common set of message types for APIs to use.

An object containing fields of an arbitrary type. An additional field `"@type"` contains a URI identifying the type. Example: `{ "id": 1234, "@type": "types.example.com/standard/id" }`.

| JSON representation |
| --- |
| ```<br>{<br>  "code": integer,<br>  "message": string,<br>  "details": [<br>    {<br>      "@type": string,<br>      field1: ...,<br>      ...<br>    }<br>  ]<br>}<br>``` |

Was this helpful?



 Send feedback



Except as otherwise noted, the content of this page is licensed under the [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/), and code samples are licensed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0). For details, see the [Google Developers Site Policies](https://developers.google.com/site-policies). Java is a registered trademark of Oracle and/or its affiliates.

Last updated 2024-09-24 UTC.


Need to tell us more?


\[\[\["Easy to understand","easyToUnderstand","thumb-up"\],\["Solved my problem","solvedMyProblem","thumb-up"\],\["Other","otherUp","thumb-up"\]\],\[\["Missing the information I need","missingTheInformationINeed","thumb-down"\],\["Too complicated / too many steps","tooComplicatedTooManySteps","thumb-down"\],\["Out of date","outOfDate","thumb-down"\],\["Samples / code issue","samplesCodeIssue","thumb-down"\],\["Other","otherDown","thumb-down"\]\],\["Last updated 2024-09-24 UTC."\],\[\],\[\]\]