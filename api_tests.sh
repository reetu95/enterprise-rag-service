#!/bin/bash

echo "----------------------------"
echo "Testing Root Endpoint"
echo "----------------------------"
curl -X GET http://127.0.0.1:8000/
echo -e "\n"


echo "----------------------------"
echo "Testing File Upload"
echo "----------------------------"
curl -X POST http://127.0.0.1:8000/uploadfile/ \
  -F "file=@obama.txt"
echo -e "\n"


echo "----------------------------"
echo "Testing Ask Endpoint"
echo "----------------------------"
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is a Retrieval-Augmented Generation system?"}'
echo -e "\n"