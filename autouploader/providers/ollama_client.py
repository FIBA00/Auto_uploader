import os
import json
import requests
from dotenv import load_dotenv
from formatters import clean_json_block

# Load environment variables
load_dotenv()


"""
Previous attemps

comand = curl http://127.0.0.1:5000/v1/models
result = {"object":"list","data":[{"id":"mistral:7b","object":"model","created":1770000012,"owned_by":"library"},{"id":"phi3:mini","object":"model","created":1770000012,"owned_by":"library"}]}


"""

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:5000")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", 60))  # seconds


class OllamaClient:
    def __init__(self, host=OLLAMA_HOST, model=OLLAMA_MODEL, timeout=OLLAMA_TIMEOUT):
        self.host = host.rstrip("/")  # remove trailing slash if any
        self.model = model
        self.timeout = timeout

    def list_models(self):
        """Get a list of available models"""
        url = f"{self.host}/v1/models"
        try:
            r = requests.get(url, timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def connect_to_model(self, model_name=None):
        """Connect to a specific model"""
        model_name = model_name or self.model
        url = f"{self.host}/v1/models/{model_name}"
        try:
            r = requests.get(url, timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def generate_chat_completion(self, payload):
        """Generate a chat completion"""
        url = f"{self.host}/v1/chat/completions"
        try:
            # Ensure model is in payload if not present
            if "model" not in payload:
                payload["model"] = self.model

            # Check if streaming is requested
            stream = payload.get("stream", False)

            r = requests.post(url, json=payload, timeout=self.timeout, stream=stream)
            r.raise_for_status()

            if stream:
                return self._parse_streaming_response(r)
            else:
                return r.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def stream_to_file(
        self, stream, file_path, prefix=None, suffix=None, is_json=False
    ):
        """
        Writes the stream to a file.

        Args:
            stream: The generator from generate_chat_completion
            file_path: The full path to save the file
            prefix: Optional string to write before the content
            suffix: Optional string to write after the content
            is_json: If True, attempts to strip Markdown code blocks usually added by LLMs
        """
        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        full_content = []

        # If we need to process the JSON (strip code blocks), we must buffer the content first.
        # Simple streaming works for writing straight to file, but removing wrapper chars
        # specifically requires seeing the edges or accumulating content.
        # To keep it simple and robust for small responses: accumulate -> clean -> write.

        # However, for true streaming visibility on console, we want to yield as we go.
        # Compromise: We yield raw chunks for console, but we buffer for file writing if valid JSON processing is needed.

        for chunk in stream:
            full_content.append(chunk)
            yield chunk

        # After stream finishes, process content for file writing
        text_content = "".join(full_content)

        if is_json:
            # Use the extracted formatter
            text_content = clean_json_block(text_content)

        # Write final processed content to file
        with open(file_path, "w", encoding="utf-8") as f:
            if prefix:
                f.write(prefix)

            f.write(text_content)

            if suffix:
                f.write(suffix)

    def _parse_streaming_response(self, response):
        """Yields content chunks from a streaming response"""
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                if decoded_line.startswith("data: "):
                    data_str = decoded_line[6:]  # Strip "data: "
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        content = (
                            data.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content", "")
                        )
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        pass

    def post_process_json(self, format_type, output_file):
        # 6. JSON Post-Processing / Validation
        if format_type == "json":
            print("\n\n🔍 JSON Post-Processing Check...")
            try:
                # We read the cleaned file back
                with open(output_file, "r") as f:
                    data = json.load(f)

                print("✅ Success! Valid JSON parsed.")
                print(f"📊 Extracted Keys: {list(data.keys())}")
                if "cost" in data:
                    print(f"💰 Detected Cost: ${data['cost']}")

            except json.JSONDecodeError as e:
                print(f"❌ JSON Validation Failed: {e}")
                # Debug info
                with open(output_file, "r") as f:
                    print(f"File content was: {f.read()}")


# Example usage
if __name__ == "__main__":
    client = OllamaClient()
    models = client.list_models()
    print("Available models:", models)
    # models is object so you can parse it as needed
    for model in models.get("data", []):
        print(f"Model: - {model['id']}")

    model_info = client.connect_to_model()
    print(f"Model info for {OLLAMA_MODEL}:", model_info)
