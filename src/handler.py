import time
import runpod
import requests
from requests.adapters import HTTPAdapter, Retry

LOCAL_URL = "http://127.0.0.1:3000/sdapi/v1"

automatic_session = requests.Session()
retries = Retry(total=10, backoff_factor=0.1, status_forcelist=[502, 503, 504])
automatic_session.mount('http://', HTTPAdapter(max_retries=retries))


# ---------------------------------------------------------------------------- #
#                              Automatic Functions                             #
# ---------------------------------------------------------------------------- #
def wait_for_service(url):
    """
    Check if the service is ready to receive requests.
    """
    retries = 0

    while True:
        try:
            requests.get(url, timeout=120)
            return
        except requests.exceptions.RequestException:
            retries += 1

            # Only log every 15 retries so the logs don't get spammed
            if retries % 15 == 0:
                print("Service not ready yet. Retrying...")
        except Exception as err:
            print("Error: ", err)

        time.sleep(0.2)


def run_txt2img(inference_request):
    """
    Run text-to-image inference.
    """
    response = automatic_session.post(url=f'{LOCAL_URL}/txt2img',
                                      json=inference_request, timeout=90)
    return response.json()


def run_img2img(inference_request):
    """
    Run image-to-image inference.
    """
    response = automatic_session.post(url=f'{LOCAL_URL}/img2img',
                                      json=inference_request, timeout=90)
    return response.json()


def get_loras():
    """
    Get available loras.
    """
    response = automatic_session.get(url=f'{LOCAL_URL}/loras', timeout=60)
    return response.json()


def get_options():
    """
    Get current options/settings.
    """
    response = automatic_session.get(url=f'{LOCAL_URL}/options', timeout=60)
    return response.json()


def set_options(options):
    """
    Set options/settings.
    """
    response = automatic_session.post(url=f'{LOCAL_URL}/options',
                                      json=options, timeout=60)
    return response.json() if response.text else {"status": "success"}


# ---------------------------------------------------------------------------- #
#                                RunPod Handler                                #
# ---------------------------------------------------------------------------- #
def handler(event):
    """
    This is the handler function that will be called by the serverless.
    Supports multiple API endpoints based on the 'api' field in the input.
    """
    input_data = event["input"]
    api_endpoint = input_data.get("api", "txt2img")
    
    try:
        if api_endpoint == "txt2img":
            # Remove 'api' field from input before sending to API
            api_input = {k: v for k, v in input_data.items() if k != "api"}
            return run_txt2img(api_input)
        
        elif api_endpoint == "img2img":
            # Remove 'api' field from input before sending to API
            api_input = {k: v for k, v in input_data.items() if k != "api"}
            return run_img2img(api_input)
        
        elif api_endpoint == "getLoras":
            return get_loras()
        
        elif api_endpoint == "getOptions":
            return get_options()
        
        elif api_endpoint == "setOptions":
            # Remove 'api' field from input before sending to API
            options = {k: v for k, v in input_data.items() if k != "api"}
            return set_options(options)
        
        else:
            return {"error": f"Unsupported API endpoint: {api_endpoint}"}
    
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Handler error: {str(e)}"}


if __name__ == "__main__":
    wait_for_service(url=f'{LOCAL_URL}/sd-models')
    print("WebUI API Service is ready. Starting RunPod Serverless...")
    runpod.serverless.start({"handler": handler})