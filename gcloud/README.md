### 

https://docs.cloud.google.com/pubsub/docs/overview

 
## Configure push notifications in Gmail API
https://developers.google.com/workspace/gmail/api/guides/push#prereqs


- 1) install gcloud cli
https://docs.cloud.google.com/sdk/docs/install-sdk
- 2) Install Pub/Sub client library
https://docs.cloud.google.com/pubsub/docs/reference/libraries#client-libraries-install-python
- 3) Enable Pub/Sub API in the gcloud console for the selected project
https://console.developers.google.com/apis/api/pubsub.googleapis.com/overview?project=<project_id>
- 4) Create Pub/Sub topic
https://docs.cloud.google.com/pubsub/docs/reference/libraries#client-libraries-install-python
- 5) Grant publish rights on the topic
https://developers.google.com/workspace/gmail/api/guides/push#grant-publish
- 6) Make a publicly accessible HTTPS URL to receive messages
    - use zrok tunnel
- 7) Create a subscribtion in the gcloud console using the publicly accessible HTTPS URL created above
- 8) Setup subscribtion authentication
https://docs.cloud.google.com/pubsub/docs/authenticate-push-subscriptions
- 7) Setup GmailClient API to call watch()
    - Enable GmailAPI in GCP
    - Setup OAuth Consent screen and use credentials.json to run gmail_auth.py
    - https://developers.google.com/workspace/gmail/api/reference/rest/v1/users/watch
    - https://developers.google.com/workspace/guides/configure-oauth-consent


## References

https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html
https://googleapis.github.io/google-api-python-client/docs/dyn/gmail_v1.users.messages.html
https://developers.google.com/workspace/gmail/api/reference/rest

### RUN

uv run uvicorn api:app --host 0.0.0.0 --port 8006 --reload