variable "REGISTRY" {
    default = "docker.io"
}

variable "REGISTRY_USER" {
    default = "leexw"
}

variable "APP" {
    default = "runpod-serverless-a1111"
}

variable "MODEL_NAME" {
    default = "sdxl"
}

variable "GIT_VERSION" {
    default = "v1.9.3"
}

target "default" {
    dockerfile = "Dockerfile.local"
    platforms = ["linux/amd64"]
    tags = ["${REGISTRY}/${REGISTRY_USER}/${APP}:${MODEL_NAME}.${GIT_VERSION}.runpod_post3"]
    args = {
        APP_NAME = "${APP}"
        MODEL_NAME = "${MODEL_NAME}"
        GIT_VERSION = "${GIT_VERSION}"
        GIT_REPO_URL = "https://github.com/AUTOMATIC1111/stable-diffusion-webui.git"
    }
}
