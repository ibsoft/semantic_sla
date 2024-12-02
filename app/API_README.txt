
Upload Document:
curl -X POST -F"tc_doc_id=1" -F "files=@SKLAVENITIS_CONTRACT.pdf" -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczMzE1NTQxNSwianRpIjoiZjUyMzUxNzAtY2Y2OS00YWY5LWE5ZGQtMGJjMDdmZTI1NDEyIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImRlbW8iLCJuYmYiOjE3MzMxNTU0MTUsImNzcmYiOiIyOGZlNjUyMi1lNTEzLTQyMzAtOTdmMS1mMGViYjJiMWMwNDMiLCJleHAiOjE3MzM1MTU0MTV9.60kVVpmn4NxJGhU2MJtlPeB8qEYExItlw0vEhdQThS0" http://localhost:5000/api/v1/upload-documents
{
  "msg": "Documents uploaded and indexed successfully."
}

Delete Document:

curl -X DELETE \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczMzE1NTQxNSwianRpIjoiZjUyMzUxNzAtY2Y2OS00YWY5LWE5ZGQtMGJjMDdmZTI1NDEyIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImRlbW8iLCJuYmYiOjE3MzMxNTU0MTUsImNzcmYiOiIyOGZlNjUyMi1lNTEzLTQyMzAtOTdmMS1mMGViYjJiMWMwNDMiLCJleHAiOjE3MzM1MTU0MTV9.60kVVpmn4NxJGhU2MJtlPeB8qEYExItlw0vEhdQThS0" \
  "http://localhost:5000/api/v1/delete-document?tc_doc_id=1"

Update Document:

curl -X PUT \
  -F "tc_doc_id=1" \
  -F "files=@Updated_Document.pdf" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczMzE1NTQxNSwianRpIjoiZjUyMzUxNzAtY2Y2OS00YWY5LWE5ZGQtMGJjMDdmZTI1NDEyIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImRlbW8iLCJuYmYiOjE3MzMxNTU0MTUsImNzcmYiOiIyOGZlNjUyMi1lNTEzLTQyMzAtOTdmMS1mMGViYjJiMWMwNDMiLCJleHAiOjE3MzM1MTU0MTV9.60kVVpmn4NxJGhU2MJtlPeB8qEYExItlw0vEhdQThS0" \
  http://localhost:5000/api/v1/update-document
