#  Cloud-Based Cat Image Segregator

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Oracle Cloud](https://img.shields.io/badge/Oracle_Cloud-Always_Free-orange?logo=oracle)
![AI](https://img.shields.io/badge/AI-OpenAI_CLIP-green)

A fully automated, serverless-style data pipeline that fetches cat images, analyzes their visual "vibe" using Machine Learning (CLIP), and segregates them into cloud storage buckets. Hosted for **$0/month** on Oracle Cloud Infrastructure (OCI).

##  Architecture

```mermaid
graph TD
    A[The Cat API] -->|Fetch Images| B(Python Script on OCI Ampere VM)
    B -->|Pixel Analysis| C{Warmth?}
    B -->|OpenAI CLIP| D{Funniness?}
    C -->|Warm/Cool| E[OCI Object Storage]
    D -->|Funny/Normal| E
    E -->|Upload Success| F[Discord Notification]
